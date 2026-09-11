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
const BRANCH_RE = /^claude\/mcp-\d{4}-\d{2}-\d{2}$/;

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
	) {}

	/** Dosyayi verilen daldan okur. Yoksa null doner (hata degil). */
	async readFile(path: string, ref?: string): Promise<string | null> {
		try {
			const res = await this.octokit.rest.repos.getContent({
				owner: this.ref.owner,
				path,
				ref: ref ?? this.ref.base,
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
	 * Biriken degisikliklerin durdugu dal — YOKSA null, olusturmaz.
	 *
	 * PR'a DEGIL DALIN KENDISINE bakar. Onceki surum acik PR ariyordu, ama
	 * yazmalar submit_for_review'dan ONCE oluyor: PR henuz yokken her cagri
	 * kendine yeni bir dal aciyor, hicbiri birikmiyordu.
	 */
	async existingBranch(): Promise<string | null> {
		const { data } = await this.octokit.rest.git.listMatchingRefs({
			owner: this.ref.owner,
			ref: `heads/${BRANCH_PREFIX}`,
			repo: this.ref.repo,
		});

		const names = data
			.map((r) => r.ref.replace("refs/heads/", ""))
			.filter((n) => BRANCH_RE.test(n))
			.sort()
			.reverse(); // tarih adin icinde; en yenisi basta

		for (const name of names) {
			// main'e gore ilerlemis mi? Birlestirilmis eski bir dal yeniden
			// kullanilmamali, yoksa kapali bir PR'a yazmaya calisiriz.
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
	 * Calisma dali: varsa mevcut olani, yoksa bugunun dalini acar. Boylece
	 * oturum boyunca (ve ayni gun icinde) tum yazmalar TEK dalda birikir ve
	 * tek PR olarak sunulur.
	 */
	async ensureBranch(): Promise<string> {
		const existing = await this.existingBranch();
		if (existing) return existing;

		const name = `${BRANCH_PREFIX}${new Date().toISOString().slice(0, 10)}`;
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
			// 422 = dal zaten var (bugun acilip birlestirilmis olabilir).
			// Uzerine yazmak dogru: yeniden ilerlemis hale gelir.
			if (err?.status !== 422) throw err;
		}
		return name;
	}

	/** JSON dosyasini calisma dalina yazar (varsa uzerine). Dal adini doner. */
	async writeJson(path: string, value: unknown, message: string): Promise<string> {
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
