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

		this.server.tool(
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
				}));
				return ok(JSON.stringify({ gosterilen: out.length, toplam: rows.length, satirlar: out }, null, 1));
			},
		);

		this.server.tool(
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

		this.server.tool(
			"list_pending_changes",
			"Henuz birlestirilmemis (PR'daki veya PR'a girecek) degisiklikleri listeler. " +
				"Yazmadan once buna bak ki ayni dosyayi iki kez yazmayasin.",
			{},
			async () => {
				const repo = this.repo();
				const branch = await repo.existingBranch();
				if (!branch) return ok("Bekleyen degisiklik yok; calisma dali temiz.");
				const files = await repo.pendingFiles();
				return ok(
					JSON.stringify({ dal: branch, degisen_dosyalar: files }, null, 1),
				);
			},
		);

		if (!canWrite) {
			this.server.tool(
				"whoami",
				"Oturum acan GitHub kullanicisini ve yetkisini soyler.",
				{},
				async () =>
					ok(
						`GitHub: ${writer}. Bu depoya YAZMA yetkin yok — yalnizca okuma ` +
							`araclari acik.`,
					),
			);
			return;
		}

		/* ------------------------------------------------------------ YAZMA */

		this.server.tool(
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

		this.server.tool(
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

		this.server.tool(
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

		this.server.tool(
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

		this.server.tool(
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

		this.server.tool(
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

		this.server.tool(
			"whoami",
			"Oturum acan GitHub kullanicisini ve yetkisini soyler.",
			{},
			async () => ok(`GitHub: ${writer} — okuma ve yazma yetkisi var.`),
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
