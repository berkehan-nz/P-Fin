/**
 * GitHub deposu = TEK VERI KAYNAGI.
 *
 * Bu sunucu hicbir sey saklamaz. Okumalar main dalindan, yazmalar tek bir
 * CALISMA DALINA gider ve oradan tek bir PR acilir. Boylece:
 *
 *   - "tum durum dosyada tutulur" ilkesi bozulmaz,
 *   - her degisiklik bir commit oldugu icin denetim izi kendiliginden olusur,
 *   - Berke tek bir yerden (PR'in Files changed sekmesi) hepsini gorur,
 *   - PR uzerinde CI calisir; sema dogrulamasi gercek Python koduyla yapilir.
 *
 * Yazmalar dogrudan main'e gitmez. Bir analiz metni yanlis olabilir; geri
 * almanin yolu "revert commit" degil, "PR'i kapat" olmali.
 */
import { Octokit } from "octokit";

/**
 * Dal oneki DAR olmali. Depoda baska projelere ait "claude/..." dallari da
 * var (ornegin claude/new-private-project-*); genis bir onekle eslesirsek
 * sunucu alakasiz bir dalin ustune yazar. Bu onek yalnizca bu sunucunun
 * acdigi dallara uyar.
 */
const BRANCH_PREFIX = "claude/mcp-";
// Yeni bicim: claude/mcp-<tarih>-<oturum>. Eski bicim (yalnizca tarih)
// hala taninir ki yarim kalmis eski dallar list_pending_changes'te gorunsun.
const BRANCH_RE = /^claude\/mcp-(\d{4}-\d{2}-\d{2})(?:-([a-z0-9]{4,12}))?$/;

/**
 * HER SOHBET OTURUMU KENDI DALINI GUNCEL MAIN'DEN ACAR.
 *
 * Gecmis: ilk surum "main'den ileride olan HERHANGI bir dali" yeniden
 * kullaniyordu ve 11 Eylul'de acilan claude/mcp-2026-09-11, 17 gun boyunca
 * her yazmanin hedefi oldu. Dal main'in 206 commit gerisine dustu; PR #1
 * 47 dosyada cakisti. Ikinci surum gunluk dal actı; ayni gun iki sohbet
 * yine ayni dala yaziyor, birinin gondermedigi degisiklik digerinin PR'ina
 * karisiyordu.
 *
 * Kural: dal adi oturum kimligini tasir (claude/mcp-2026-09-28-a1b2c3).
 * Bir oturum YALNIZCA kendi dalina yazar ve yalnizca kendi dalini gonderir.
 * Baska oturumlardan kalan, gonderilmemis dallar list_pending_changes'te
 * ayrica bildirilir ki kaybolmasin.
 */
function branchSession(name: string): string | null {
	const m = BRANCH_RE.exec(name);
	return m ? (m[2] ?? null) : null;
}

function todayUtc(): string {
	return new Date().toISOString().slice(0, 10);
}

/** Oturum kimliginden dal etiketi: kucuk harf + rakam, 6 karakter. */
export function sessionTag(sessionId: string): string {
	const clean = sessionId.toLowerCase().replace(/[^a-z0-9]/g, "");
	return (clean.slice(0, 6) || "x").padEnd(4, "0");
}

/**
 * MCP'NIN YAZABILECEGI DOSYALAR — beyaz liste.
 *
 * Kural: MCP otomasyonun yazdigi hicbir dosyaya DOKUNMAZ. Tarama, gunluk
 * kosu, nabiz ve Merge is akisi data/cards/, data/candidates.json ve
 * benzerlerini surekli yeniden yaziyor; MCP de yazarsa her PR cakisir.
 *
 * Asagidakiler yalnizca KULLANICI NIYETI tasir ve hicbir otomasyon
 * bunlara yazmaz (git gecmisiyle dogrulandi):
 *   claude_inbox/<T>.json  analiz, karar, katalizor puani
 *   data/portfolio.json    pozisyonlar (elle girilen islem kayitlari)
 *   data/watchlist.json    izleme listesi
 *   data/overrides.json    ham veri duzeltmeleri (kaynakli)
 *   data/tr_macro.json     TCMB faizi, TUFE, erken secim (elle, kaynakli)
 *
 * Yeni bir arac baska bir yola yazmaya calisirsa REDDEDILIR — sorunun
 * sessizce geri gelmesi yerine yuksek sesle basarisiz olur.
 */
const WRITABLE_PATHS: RegExp[] = [
	/^claude_inbox\/[A-Z0-9.\-]+\.json$/,
	/^data\/(portfolio|watchlist|overrides|tr_macro)\.json$/,
];

export function isWritablePath(path: string): boolean {
	return WRITABLE_PATHS.some((re) => re.test(path));
}

export type RepoRef = { owner: string; repo: string; base: string };

export function parseRepo(full: string, base = "main"): RepoRef {
	const [owner, repo] = full.split("/");
	if (!owner || !repo) {
		throw new Error(`GITHUB_REPO 'sahip/depo' biciminde olmali, '${full}' geldi`);
	}
	return { base, owner, repo };
}

export class Repo {
	constructor(
		private octokit: Octokit,
		private ref: RepoRef,
		/** Bu sohbet oturumunun dal etiketi (sessionTag). */
		private session: string,
	) {}

	/** Bu oturumun dal adi (bugun acilirsa). */
	private branchName(): string {
		return `${BRANCH_PREFIX}${todayUtc()}-${this.session}`;
	}

	/**
	 * Depo PUBLIC oldugu icin okumalar jeton istemez.
	 *
	 * Neden onemli: GitHub bir OAuth uygulamasi icin kullanici basina jeton
	 * sayisi asilinca EN ESKISINI iptal eder. Jeton olunce okuma araclari da
	 * kilitleniyordu — oysa okunan her sey zaten herkese acik. Artik jeton
	 * YALNIZCA YAZMA icin gerekli; 401 bir daha list_candidates'i durdurmaz.
	 *
	 * Yalnizca `main` icin kullanilir: raw CDN birkac dakika onbelleklidir ve
	 * CALISMA DALINDAN okurken bayat icerik ajanin kendi yazdigini ezmesine
	 * yol acar. Dal okumalari API'den (taze) yapilir.
	 */
	private async readRaw(path: string, ref: string): Promise<string | null> {
		const url = `https://raw.githubusercontent.com/${this.ref.owner}/${this.ref.repo}/${ref}/${path}`;
		const res = await fetch(url, { headers: { "User-Agent": "pfin-mcp" } });
		if (res.status === 404) return null;
		if (!res.ok) throw Object.assign(new Error(`raw ${res.status} ${path}`), {
			status: res.status,
		});
		return await res.text();
	}

	/** Dosyayi verilen daldan okur. Yoksa null doner (hata degil). */
	async readFile(path: string, ref?: string): Promise<string | null> {
		const target = ref ?? this.ref.base;
		if (target === this.ref.base) {
			// main: once jetonsuz raw; CDN/ag sorunlarinda API'ye dus.
			try {
				return await this.readRaw(path, target);
			} catch {
				/* API'ye dusulecek */
			}
		}
		return await this.readViaApi(path, target);
	}

	private async readViaApi(path: string, ref: string): Promise<string | null> {
		try {
			const res = await this.octokit.rest.repos.getContent({
				owner: this.ref.owner,
				path,
				ref,
				repo: this.ref.repo,
			});
			const data = res.data as { content?: string; encoding?: string };
			if (!data.content) return null;
			// atob ikili guvenli degil; UTF-8 metin icin TextDecoder sart,
			// aksi halde Turkce karakterler bozulur.
			const bytes = Uint8Array.from(atob(data.content.replace(/\n/g, "")), (c) =>
				c.charCodeAt(0),
			);
			return new TextDecoder().decode(bytes);
		} catch (err: any) {
			if (err?.status === 404) return null;
			throw err;
		}
	}

	async readJson<T = any>(path: string, ref?: string): Promise<T | null> {
		const text = await this.readFile(path, ref);
		return text === null ? null : (JSON.parse(text) as T);
	}

	/**
	 * Bu oturumun, henuz birlestirilmemis dali — YOKSA null, olusturmaz.
	 *
	 * Yalnizca BU OTURUMUN etiketini tasiyan dallar aday. Gece yarisini
	 * geçen bir sohbet dunku tarihli kendi dalina yazmaya devam eder.
	 */
	async existingBranch(): Promise<string | null> {
		const { data } = await this.octokit.rest.git.listMatchingRefs({
			owner: this.ref.owner,
			ref: `heads/${BRANCH_PREFIX}`,
			repo: this.ref.repo,
		});

		const names = data
			.map((r) => r.ref.replace("refs/heads/", ""))
			.filter((n) => branchSession(n) === this.session)
			.sort()
			.reverse(); // tarih adin icinde; en yenisi basta

		for (const name of names) {
			// main'e gore ilerlemis mi? Birlestirilmis dal yeniden
			// kullanilmaz, yoksa kapali bir PR'a yazmaya calisiriz.
			const { data: cmp } = await this.octokit.rest.repos.compareCommitsWithBasehead({
				basehead: `${this.ref.base}...${name}`,
				owner: this.ref.owner,
				repo: this.ref.repo,
			});
			if ((cmp.ahead_by ?? 0) > 0) return name;
		}
		return null;
	}

	/**
	 * BASKA oturumlardan kalan, birlestirilmemis dallar.
	 *
	 * Bunlar sessizce unutulmamali: icinde gercek kararlar olabilir.
	 * list_pending_changes bunlari ayrica bildirir ki kullanici ya PR acsin
	 * ya da silsin.
	 */
	async staleBranches(): Promise<{ name: string; ahead: number; behind: number }[]> {
		const { data } = await this.octokit.rest.git.listMatchingRefs({
			owner: this.ref.owner,
			ref: `heads/${BRANCH_PREFIX}`,
			repo: this.ref.repo,
		});
		const out: { name: string; ahead: number; behind: number }[] = [];
		for (const r of data) {
			const name = r.ref.replace("refs/heads/", "");
			if (!BRANCH_RE.test(name)) continue;
			if (branchSession(name) === this.session) continue;
			const { data: cmp } = await this.octokit.rest.repos.compareCommitsWithBasehead({
				basehead: `${this.ref.base}...${name}`,
				owner: this.ref.owner,
				repo: this.ref.repo,
			});
			if ((cmp.ahead_by ?? 0) > 0) {
				out.push({ ahead: cmp.ahead_by ?? 0, behind: cmp.behind_by ?? 0, name });
			}
		}
		return out;
	}

	/**
	 * Calisma dali: bu oturumun acik dali varsa o, yoksa GUNCEL MAIN'den
	 * yeni bir dal. Oturum boyunca tum yazmalar tek dalda birikir ve tek PR
	 * olarak sunulur.
	 */
	async ensureBranch(): Promise<string> {
		const existing = await this.existingBranch();
		if (existing) return existing;

		const name = this.branchName();
		const { data: baseRef } = await this.octokit.rest.git.getRef({
			owner: this.ref.owner,
			ref: `heads/${this.ref.base}`,
			repo: this.ref.repo,
		});
		try {
			await this.octokit.rest.git.createRef({
				owner: this.ref.owner,
				ref: `refs/heads/${name}`,
				repo: this.ref.repo,
				sha: baseRef.object.sha,
			});
		} catch (err: any) {
			// 422 = dal zaten var. Iki durum:
			//  - Ayni oturumun ES ZAMANLI bir cagrisi az once acti (main'le
			//    ayni ya da ileride): oldugu gibi kullan, SIFIRLAMA — yoksa
			//    o cagrinin commit'i silinir.
			//  - Bu oturumun bugun acip PR'i BIRLESMIS dali (ileride degil,
			//    main'in gerisinde): icerigi zaten main'de; guncel main'e cek.
			if (err?.status !== 422) throw err;
			const { data: cmp } = await this.octokit.rest.repos.compareCommitsWithBasehead({
				basehead: `${this.ref.base}...${name}`,
				owner: this.ref.owner,
				repo: this.ref.repo,
			});
			if ((cmp.ahead_by ?? 0) === 0 && (cmp.behind_by ?? 0) > 0) {
				await this.octokit.rest.git.updateRef({
					force: true,
					owner: this.ref.owner,
					ref: `heads/${name}`,
					repo: this.ref.repo,
					sha: baseRef.object.sha,
				});
			}
		}
		return name;
	}

	/** JSON dosyasini calisma dalina yazar (varsa uzerine). Dal adini doner. */
	async writeJson(path: string, value: unknown, message: string): Promise<string> {
		if (!isWritablePath(path)) {
			throw new Error(
				`'${path}' otomasyona ait bir dosya; MCP buraya yazamaz. ` +
					"Kartlar ve aday listesi veri hattinin isidir — analiz " +
					"claude_inbox/'a yazilir, PR birlesince Merge is akisi kartlari uretir.",
			);
		}
		const branch = await this.ensureBranch();
		const body = `${JSON.stringify(value, null, 2)}\n`;

		// Dosyanin O DALDAKI sha'si gerekir; main'deki sha ile yazmak
		// ayni dalda ikinci yazmada catisma verir.
		let sha: string | undefined;
		try {
			const res = await this.octokit.rest.repos.getContent({
				owner: this.ref.owner,
				path,
				ref: branch,
				repo: this.ref.repo,
			});
			sha = (res.data as { sha?: string }).sha;
		} catch (err: any) {
			if (err?.status !== 404) throw err;
		}

		const bytes = new TextEncoder().encode(body);
		let binary = "";
		bytes.forEach((b) => {
			binary += String.fromCharCode(b);
		});

		await this.octokit.rest.repos.createOrUpdateFileContents({
			branch,
			content: btoa(binary),
			message,
			owner: this.ref.owner,
			path,
			repo: this.ref.repo,
			sha,
		});
		return branch;
	}

	/** Calisma dalinin main'e gore degistirdigi dosyalar. */
	async pendingFiles(): Promise<string[]> {
		const branch = await this.existingBranch();
		if (!branch) return [];
		const { data } = await this.octokit.rest.repos.compareCommitsWithBasehead({
			basehead: `${this.ref.base}...${branch}`,
			owner: this.ref.owner,
			repo: this.ref.repo,
		});
		return (data.files ?? []).map((f) => f.filename);
	}

	/**
	 * GERCEK kimlik dogrulama — jetonla bir GitHub cagrisi yapar.
	 *
	 * Onceki `whoami` hicbir cagri yapmadan "yazma yetkin var" diyordu:
	 * OAuth oturumundaki login adini tekrarliyordu. Jeton iptal edilmisken
	 * bile ayni cumleyi kuruyor, kullanici ancak ilk yazma denemesinde
	 * ogreniyordu. Bir durum aracinin yalan soylemesi, hic olmamasindan
	 * kotudur.
	 */
	async verify(): Promise<{ login: string; canPush: boolean; repo: string }> {
		const { data: user } = await this.octokit.rest.users.getAuthenticated();
		const { data: repo } = await this.octokit.rest.repos.get({
			owner: this.ref.owner,
			repo: this.ref.repo,
		});
		return {
			canPush: repo.permissions?.push ?? false,
			login: user.login,
			repo: repo.full_name,
		};
	}

	/** Tek PR'i acar veya basligini/govdesini gunceller. */
	async submit(title: string, body: string) {
		const branch = await this.existingBranch();
		if (!branch) return null;

		const { data: open } = await this.octokit.rest.pulls.list({
			base: this.ref.base,
			head: `${this.ref.owner}:${branch}`,
			owner: this.ref.owner,
			repo: this.ref.repo,
			state: "open",
		});

		if (open.length > 0) {
			const { data } = await this.octokit.rest.pulls.update({
				body,
				owner: this.ref.owner,
				pull_number: open[0].number,
				repo: this.ref.repo,
				title,
			});
			return { created: false, number: data.number, url: data.html_url };
		}

		const { data } = await this.octokit.rest.pulls.create({
			base: this.ref.base,
			body,
			head: branch,
			owner: this.ref.owner,
			repo: this.ref.repo,
			title,
		});
		return { created: true, number: data.number, url: data.html_url };
	}
}
