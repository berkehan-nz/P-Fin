/**
 * P-Fin MCP — Claude Chat'in finansal takip sistemini yonetmesi icin.
 *
 * TASARIM ILKESI (README'deki ile ayni): yazan taraf SAYISAL ALANLARA
 * DOKUNAMAZ. Analiz metni ve karar serbesttir; metrikler, fiyatlar ve
 * puanlar veri hattinin sorumlulugundadir. Veride gercekten hata varsa
 * duzeltme METRIGE degil HAM DONEM VERISINE yazilir (report_data_issue) ve
 * kaynak zorunludur — sonra her sey yeniden hesaplanir.
 *
 * AKIS: her yazma tek bir calisma dalina commit olur -> submit_for_review
 * tek bir PR acar -> CI semayi gercek Python koduyla dogrular -> Berke
 * PR'i birlestirir -> Merge is akisi kartlari gunceller -> Pages yayinlar.
 */
import OAuthProvider from "@cloudflare/workers-oauth-provider";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { McpAgent } from "agents/mcp";
import { Octokit } from "octokit";
import { z } from "zod";
import { GitHubHandler } from "./github-handler";
import {
	actionSchema,
	OVERRIDABLE_FIELDS,
	pruneEmpty,
	storySchema,
	tickerSchema,
	today,
} from "./pfin/contract";
import { parseRepo, Repo } from "./pfin/repo";
import type { Props } from "./utils";

const ok = (text: string) => ({ content: [{ text, type: "text" as const }] });
const fail = (text: string) => ({
	content: [{ text, type: "text" as const }],
	isError: true,
});

export class PFinMCP extends McpAgent<Env, Record<string, never>, Props> {
	server = new McpServer({
		name: "P-Fin — Berkehan finansal takip sistemi",
		version: "1.0.0",
	});

	/**
	 * Arac kaydi + GitHub hata cevirisi.
	 *
	 * "Bad credentials" (401) ajana hicbir sey anlatmiyordu ve bazi araclar
	 * calisirken digerleri bu hatayi veriyordu. Olasi sebep: GitHub bir OAuth
	 * uygulamasi icin kullanici basina ~10 jetonu gecince EN ESKISINI iptal
	 * eder; baglayici birden fazla oturum actiginda eski oturumdaki jeton
	 * gecersiz kalir. Hata artik ne yapilacagini soyluyor.
	 */
	private tool(name: string, description: string, schema: any, handler: (args: any) => Promise<any>) {
		this.server.tool(name, description, schema, async (args: any) => {
			try {
				return await handler(args);
			} catch (err: any) {
				const status = err?.status;
				if (status === 401) {
					return fail(
						"GitHub oturum jetonu gecersiz (401). Jeton iptal edilmis olabilir — " +
							"GitHub bir uygulama icin cok sayida oturum acilinca en eskisini iptal eder. " +
							"Cozum: claude.ai > Settings > Connectors'ta P-Fin baglayicisini " +
							"kaldirip yeniden bagla. Bu bir veri hatasi degildir.",
					);
				}
				if (status === 403) {
					return fail(`GitHub erisimi reddedildi (403): ${err?.message ?? ""}. ` +
						"Hiz limiti ya da yetki kapsami olabilir; biraz bekleyip tekrar dene.");
				}
				if (status === 409 || status === 422) {
					return fail(`GitHub cakisma (${status}): ${err?.message ?? ""}. ` +
						"Ayni dosyaya es zamanli yazma olmus olabilir; list_pending_changes ile kontrol edip tekrar dene.");
				}
				return fail(`Beklenmeyen hata: ${err?.message ?? String(err)}`);
			}
		});
	}

	private repo(): Repo {
		return new Repo(
			new Octokit({ auth: this.props!.accessToken }),
			parseRepo(this.env.GITHUB_REPO ?? "berkehan-nz/P-Fin"),
		);
	}

	/** Inbox dosyasini calisma dalindan okur; yoksa main'den; yoksa bos. */
	private async inboxFor(repo: Repo, ticker: string) {
		const path = `claude_inbox/${ticker}.json`;
		const branch = await repo.existingBranch();
		const staged = branch ? await repo.readJson<any>(path, branch) : null;
		return { current: staged ?? (await repo.readJson<any>(path)) ?? { ticker }, path };
	}

	async init() {
		const writer = this.props!.login;
		const canWrite = writer === (this.env.ALLOWED_LOGIN ?? "berkehan-nz");

		/* ------------------------------------------------------------ OKUMA */

		this.tool(
			"list_candidates",
			"Adaylari puana gore siralar. Once buna bak; hangi sirketin analize " +
				"ihtiyaci oldugunu buradan gorursun.",
			{
				decision: z
					.enum(["AL", "BEKLE", "ELE", "karar_yok"])
					.optional()
					.describe("Karar durumuna gore filtrele"),
				limit: z.number().min(1).max(60).default(15),
				needs_analysis: z
					.boolean()
					.optional()
					.describe("Yalnizca Claude notu olmayan veya 30 gunden eski olanlar"),
			},
			async ({ limit, decision, needs_analysis }) => {
				const data = await this.repo().readJson<any>("data/candidates.json");
				if (!data) return fail("data/candidates.json okunamadi.");

				let rows = [
					...(data.seed ?? []),
					...(data.candidates ?? []),
					...(data.manual ?? []),
				];
				const seen = new Set<string>();
				rows = rows.filter((r) => !seen.has(r.ticker) && seen.add(r.ticker));

				if (decision === "karar_yok") rows = rows.filter((r) => !r.decision);
				else if (decision) rows = rows.filter((r) => r.decision === decision);
				if (needs_analysis) {
					rows = rows.filter(
						(r) => !r.claude_verdict || (r.story_age_days ?? 999) > 30,
					);
				}

				rows.sort((a, b) => (b.scores?.total ?? -1) - (a.scores?.total ?? -1));
				const out = rows.slice(0, limit).map((r) => ({
					decision: r.decision || null,
					karar_yasi_gun: r.story_age_days ?? null,
					kapsama: r.scores?.weight_coverage ?? null,
					name: r.name,
					puan: r.scores?.total ?? null,
					sektor: r.sector,
					ticker: r.ticker,
					uyari: r.warning_count ?? 0,
					veri_kalitesi: r.data_quality,
					// Kola gore degismeyen ortak metrikler (headline kola gore degisir).
					cekirdek: r.core ?? null,
					dusuk_kapsamali_bloklar: r.low_coverage_blocks ?? {},
					yuzdelik_havuzu: r.percentile_pool ?? null,
					fiyat_tarihi: r.price_as_of ?? null,
				}));
				return ok(JSON.stringify({ gosterilen: out.length, toplam: rows.length, satirlar: out }, null, 1));
			},
		);

		this.tool(
			"get_card",
			"Bir sirketin kartini okur. Kartlar buyuk oldugu icin bolum sec; " +
				"'ozet' puanlari, bayraklari ve veri kalitesini verir.",
			{
				section: z
					.enum(["ozet", "metrikler", "analiz", "skor_detay", "hepsi"])
					.default("ozet"),
				ticker: tickerSchema,
			},
			async ({ ticker, section }) => {
				const card = await this.repo().readJson<any>(`data/cards/${ticker}.json`);
				if (!card) return fail(`${ticker} icin kart yok. Once veri hatti calismali.`);

				const pick: Record<string, unknown> = {
					as_of: card.as_of,
					name: card.name,
					sector: card.sector,
					ticker: card.ticker,
				};
				if (section === "hepsi") return ok(JSON.stringify(card, null, 1));
				if (section === "ozet") {
					Object.assign(pick, {
						data_quality: card.data_quality,
						flags: card.flags,
						fiyat: card.price,
						overrides: card.overrides ?? [],
						piyasa_degeri_musd: card.market_cap_musd,
						scores: card.scores,
					});
				}
				if (section === "metrikler") Object.assign(pick, { metrics: card.metrics, ttm: card.ttm });
				if (section === "analiz") Object.assign(pick, { decision: card.decision, story: card.story });
				if (section === "skor_detay") {
					Object.assign(pick, {
						score_detail: card.score_detail,
						score_internals: card.score_internals,
						scores: card.scores,
					});
				}
				return ok(JSON.stringify(pick, null, 1));
			},
		);

		this.tool(
			"list_pending_changes",
			"Henuz birlestirilmemis (PR'daki veya PR'a girecek) degisiklikleri listeler. " +
				"Yazmadan once buna bak ki ayni dosyayi iki kez yazmayasin.",
			{},
			async () => {
				const repo = this.repo();
				const branch = await repo.existingBranch();
				const stale = await repo.staleBranches();
				const uyari = stale.length
					? {
							bayat_dallar: stale.map((b) =>
								`${b.name} (${b.ahead} commit ileride, ${b.behind} geride)`,
							),
							not:
								"Bu dallar 7 gunden eski oldugu icin yeni yazmalar ORAYA GITMEZ. " +
								"Icinde birlestirilmemis is olabilir: GitHub'da PR acip birlestir " +
								"ya da dali sil.",
						}
					: null;

				if (!branch) {
					return ok(
						JSON.stringify(
							{ bekleyen: "yok — calisma dali temiz", ...(uyari ?? {}) },
							null,
							1,
						),
					);
				}
				const files = await repo.pendingFiles();
				return ok(
					JSON.stringify(
						{ dal: branch, degisen_dosyalar: files, ...(uyari ?? {}) },
						null,
						1,
					),
				);
			},
		);

		if (!canWrite) {
			this.registerWhoami(writer, false);
			return;
		}

		/* ------------------------------------------------------------ YAZMA */

		this.tool(
			"write_analysis",
			"Bir sirketin analiz metnini claude_inbox'a yazar. SAYISAL ALAN YAZAMAZ — " +
				"metrikler ve puanlar veri hattinin isidir. Bos birakilan alanlar kartta " +
				"yazili olani SILMEZ. Yazdiktan sonra submit_for_review cagirmayi unutma.",
			{
				story: storySchema,
				ticker: tickerSchema,
			},
			async ({ ticker, story }) => {
				const repo = this.repo();
				const { current, path } = await this.inboxFor(repo, ticker);
				const merged = {
					...current,
					story: {
						...(current.story ?? {}),
						...pruneEmpty(story),
						author: "claude",
						updated_at: today(),
					},
					ticker,
				};
				const branch = await repo.writeJson(path, merged, `analiz: ${ticker}`);
				return ok(
					`${ticker} analizi ${branch} dalina yazildi. ` +
						`Bitirdiginde submit_for_review ile PR ac.`,
				);
			},
		);

		this.tool(
			"set_decision",
			"AL / BEKLE / ELE kararini ve gerekcesini yazar.",
			{
				action: actionSchema,
				rationale: z.string().min(10).max(4000).describe("Neden bu karar"),
				ticker: tickerSchema,
			},
			async ({ ticker, action, rationale }) => {
				const repo = this.repo();
				const { current, path } = await this.inboxFor(repo, ticker);
				const merged = {
					...current,
					decision: { action, author: "claude", date: today(), rationale },
					ticker,
				};
				const branch = await repo.writeJson(path, merged, `karar: ${ticker} ${action}`);
				return ok(`${ticker} -> ${action} (${branch}).`);
			},
		);

		this.tool(
			"set_catalyst_score",
			"Katalizor puani (0-100). Toplam puanin %25'i budur ve otomatik " +
				"hesaplanmaz — yeniden fiyatlanmayi tetikleyecek somut bir olay var mi?",
			{ score: z.number().min(0).max(100), ticker: tickerSchema },
			async ({ ticker, score }) => {
				const repo = this.repo();
				const { current, path } = await this.inboxFor(repo, ticker);
				const branch = await repo.writeJson(
					path,
					{ ...current, catalyst_score: score, ticker },
					`katalizor: ${ticker} ${score}`,
				);
				return ok(`${ticker} katalizor puani ${score} (${branch}).`);
			},
		);

		this.tool(
			"add_to_watchlist",
			"Izleme listesine sirket ekler.",
			{
				reason: z.string().min(5).max(500),
				tags: z.array(z.string().max(40)).max(8).default([]),
				ticker: tickerSchema,
			},
			async ({ ticker, reason, tags }) => {
				const repo = this.repo();
				const branch = await repo.existingBranch();
				const wl =
					(branch ? await repo.readJson<any>("data/watchlist.json", branch) : null) ??
					(await repo.readJson<any>("data/watchlist.json")) ?? { entries: [] };

				const entries = (wl.entries ?? []).filter(
					(e: any) => String(e.ticker).toUpperCase() !== ticker,
				);
				entries.push({
					active: true,
					added_by: "claude",
					added_date: today(),
					reason,
					tags,
					ticker,
				});
				const b = await repo.writeJson(
					"data/watchlist.json",
					{ ...wl, entries },
					`izleme: ${ticker}`,
				);
				return ok(`${ticker} izleme listesine eklendi (${b}).`);
			},
		);

		this.tool(
			"record_position",
			"Portfoye yeni pozisyon ekler (GERCEK veya KAGIT). Maliyet + komisyon nakitten " +
				"dusulur; nakit yetmezse yazmaz. PR ile sunulur — birlestirilene kadar " +
				"portfoy sayfasinda gorunmez.",
			{
				entry_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
				entry_price: z.number().positive(),
				fees_usd: z.number().min(0).default(0),
				notes: z.string().max(1000).default(""),
				review_date: z
					.string()
					.regex(/^\d{4}-\d{2}-\d{2}$/)
					.optional()
					.describe("Tezi yeniden gozden gecirme tarihi"),
				shares: z.number().positive(),
				target_price: z.number().min(0).default(0),
				ticker: tickerSchema,
				type: z.enum(["GERCEK", "KAGIT"]).default("KAGIT"),
			},
			async (a) => {
				const repo = this.repo();
				const branch = await repo.existingBranch();
				const doc =
					(branch ? await repo.readJson<any>("data/portfolio.json", branch) : null) ??
					(await repo.readJson<any>("data/portfolio.json")) ?? {
						cash_usd: 0, closed: [], positions: [],
					};

				const cost = a.entry_price * a.shares + a.fees_usd;
				const cash = Number(doc.cash_usd ?? 0);
				if (cost > cash + 1e-6) {
					return fail(
						`Nakit yetmiyor: pozisyon ${cost.toFixed(2)} $, portfoyde ${cash.toFixed(2)} $ nakit var. ` +
							"Hisse adedini azalt ya da once nakit ekle.",
					);
				}
				const position = {
					broker: "Midas", entry_date: a.entry_date, entry_price: a.entry_price,
					fees_usd: a.fees_usd, notes: a.notes, review_date: a.review_date ?? "",
					shares: a.shares, status: "OPEN", target_price: a.target_price,
					thesis_breakers: [], ticker: a.ticker, type: a.type,
				};
				const next = {
					...doc,
					as_of: today(),
					cash_usd: Math.round((cash - cost) * 100) / 100,
					positions: [...(doc.positions ?? []), position],
				};
				const b = await repo.writeJson("data/portfolio.json", next,
					`portfoy: ${a.type} ${a.ticker} ${a.shares} @ ${a.entry_price}`);
				return ok(
					`${a.type} ${a.ticker}: ${a.shares} adet @ ${a.entry_price} $ (maliyet ${cost.toFixed(2)} $) ` +
						`${b} dalina yazildi. Kalan nakit ${next.cash_usd.toFixed(2)} $. ` +
						`Tum pozisyonlari girdikten sonra submit_for_review ile PR ac.`,
				);
			},
		);

		this.tool(
			"report_data_issue",
			"Veride hata bulduysan HAM DONEM VERISINI duzeltir (metrigi degil) — " +
				"brut kar, hasilat, nakit gibi. Duzeltilen degerden marjlar, puanlar ve " +
				"huni karari yeniden hesaplanir. KAYNAK ZORUNLU: kaynaksiz bir sayi " +
				"duzeltme degil tahmindir. Puan/metrik alanlari duzeltilemez.",
			{
				field: z
					.enum(OVERRIDABLE_FIELDS)
					.describe("Duzeltilecek ham alan, orn. gross_profit"),
				period_end: z
					.string()
					.regex(/^(latest|\d{4}-\d{2}-\d{2})$/)
					.default("latest"),
				reason: z
					.string()
					.min(15)
					.max(600)
					.describe("Neden yanlis ve dogrusu nereden geliyor"),
				source_url: z
					.string()
					.url()
					.startsWith("http")
					.describe("SEC dosyasi veya birincil kaynak adresi"),
				ticker: tickerSchema,
				value: z.number().nullable().describe("Dogru deger (milyon USD); null = alani bosalt"),
			},
			async ({ ticker, field, period_end, value, reason, source_url }) => {
				const repo = this.repo();
				const branch = await repo.existingBranch();
				const doc =
					(branch ? await repo.readJson<any>("data/overrides.json", branch) : null) ??
					(await repo.readJson<any>("data/overrides.json")) ?? { overrides: [] };

				const list = (doc.overrides ?? []).filter(
					(o: any) =>
						!(
							String(o.ticker).toUpperCase() === ticker &&
							o.field === field &&
							o.period_end === period_end
						),
				);
				list.push({
					added_at: today(),
					author: "claude",
					field,
					period_end,
					reason,
					source_url,
					ticker,
					value,
				});

				const b = await repo.writeJson(
					"data/overrides.json",
					{ ...doc, overrides: list },
					`duzeltme: ${ticker} ${field}`,
				);
				return ok(
					`${ticker} ${period_end} ${field} = ${value} olarak kaydedildi (${b}).\n` +
						`Bu bir ONERIDIR: PR birlestirilene ve veri hatti yeniden kosana ` +
						`kadar kartta degisiklik olmaz. Kartta "ELLE DUZELTME" uyarisi ve ` +
						`kaynak gorunecek.`,
				);
			},
		);

		/* ---------------------------------------------------------- INCELEME */

		this.tool(
			"submit_for_review",
			"Biriken tum degisiklikler icin TEK bir PR acar (veya acik olani gunceller). " +
				"Berke bu PR'i birlestirdiginde degisiklikler yayina girer.",
			{
				summary: z
					.string()
					.min(20)
					.max(4000)
					.describe("Ne degisti ve neden — Berke bunu okuyup karar verecek"),
				title: z.string().min(5).max(100),
			},
			async ({ title, summary }) => {
				const repo = this.repo();
				const files = await repo.pendingFiles();
				if (files.length === 0) {
					return fail("Bekleyen degisiklik yok — once bir yazma araci kullan.");
				}
				const body =
					`${summary}\n\n---\n**Degisen dosyalar**\n` +
					files.map((f) => `- \`${f}\``).join("\n") +
					`\n\n_Claude Chat tarafindan MCP uzerinden olusturuldu. ` +
					`Sema dogrulamasi CI'da (\`src/inbox.py\`, \`src/overrides.py\`) yapilir._`;

				const pr = await repo.submit(title, body);
				if (!pr) return fail("PR acilamadi — calisma dali bulunamadi.");
				return ok(
					`${pr.created ? "PR acildi" : "Acik PR guncellendi"}: #${pr.number}\n${pr.url}\n` +
						`${files.length} dosya. Birlestirdiginde Merge is akisi kartlari gunceller.`,
				);
			},
		);

		this.registerWhoami(writer, true);
	}

	/**
	 * whoami — GERCEK dogrulama yapar, oturumdaki adi tekrarlamaz.
	 *
	 * Onceki surum hicbir GitHub cagrisi yapmadan "okuma ve yazma yetkisi var"
	 * diyordu. Jeton iptal edilmisken bile ayni cumleyi kuruyordu: ayni anda
	 * list_candidates "401" verirken whoami "her sey yolunda" diyordu.
	 * Bir durum araci yanlis guven veriyorsa, hic olmamasindan kotudur.
	 */
	private registerWhoami(sessionLogin: string, allowedByConfig: boolean) {
		this.tool(
			"whoami",
			"Oturum acan GitHub kullanicisini ve yetkisini DOGRULAR (gercek GitHub " +
				"cagrisi yapar). Yazma denemeden once buna bak.",
			{},
			async () => {
				const v = await this.repo().verify();   // 401 ise sarmalayici anlatir
				const lines = [
					`GitHub kullanicisi: ${v.login}`,
					`Depo: ${v.repo}`,
					`Jeton: GECERLI (dogrulandi)`,
				];

				if (v.login !== sessionLogin) {
					lines.push(
						`UYARI: oturumdaki ad (${sessionLogin}) jetonun sahibinden ` +
							`(${v.login}) farkli. Baglayiciyi yeniden baglaman gerekebilir.`,
					);
				}

				if (!allowedByConfig) {
					lines.push(
						`Yazma: KAPALI — bu sunucu yalnizca ALLOWED_LOGIN icin yazma ` +
							`araclarini acar. Okuma araclari calisir.`,
					);
				} else if (!v.canPush) {
					lines.push(
						`Yazma: KAPALI — GitHub bu depoda push yetkisi vermiyor. ` +
							`Jetonun kapsami dar olabilir; baglayiciyi kaldirip yeniden bagla.`,
					);
				} else {
					lines.push(`Yazma: ACIK (push yetkisi dogrulandi, PR akisiyla).`);
				}

				lines.push(
					`Not: okumalar jeton gerektirmez (depo public, raw'dan okunur); ` +
						`jeton yalnizca yazma icin kullanilir.`,
				);
				return ok(lines.join("\n"));
			},
		);
	}
}

export default new OAuthProvider({
	apiHandler: PFinMCP.serve("/mcp") as any,
	apiRoute: "/mcp",
	authorizeEndpoint: "/authorize",
	clientRegistrationEndpoint: "/register",
	defaultHandler: GitHubHandler as any,
	tokenEndpoint: "/token",
});
