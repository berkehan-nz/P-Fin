/**
 * claude_inbox sozlesmesinin TypeScript yansimasi.
 *
 * ASIL DOGRULAMA PYTHON'DA: ``src/inbox.py`` ve ``src/overrides.py``. Burasi
 * yalnizca ON ELEME yapar — bozuk bir yazmayi commit'e donusmeden once
 * reddeder ki Berke gereksiz bir PR ile ugrasmasin. Kurallar burada
 * cogaltilmaz, YANSITILIR; nihai karar PR uzerinde calisan CI'nindir.
 * Iki taraf ayrisirsa CI kazanir ve yaniliyor olan bu dosyadir.
 */
import { z } from "zod";

const MAX_TEXT = 4000;
const MAX_LIST = 12;

const text = z.string().max(MAX_TEXT);
const bullets = z.array(z.string().max(MAX_TEXT)).max(MAX_LIST);

export const storySchema = z.object({
	analyst_narrative: text.optional(),
	bear_case: bullets.optional(),
	bull_case: bullets.optional(),
	business_model: text.optional(),
	catalyst: z
		.object({
			confidence: z.enum(["dusuk", "orta", "yuksek"]).optional(),
			expected_date: z.string().max(32).optional(),
			type: text.optional(),
		})
		.optional(),
	claude_verdict: text.optional(),
	moat: text.optional(),
	news_summary: text.optional(),
	thesis_breakers: bullets.optional(),
	why_cheap_diagnosis: text.optional(),
	why_cheap_rationale: text.optional(),
});

export const tickerSchema = z
	.string()
	.regex(/^[A-Z][A-Z0-9.\-]{0,9}$/, "Sembol buyuk harf olmali, orn. YOU");

export const actionSchema = z.enum(["AL", "BEKLE", "ELE"]);

/**
 * Duzeltilebilir HAM alanlar. Metrikler, puanlar ve turetilmis alanlar
 * (fcf, financial_debt, ...) kasitli olarak DISARIDA: onlar ham veriden
 * hesaplanir, elle yazilirlarsa girdiyle cikti celisir.
 * src/fundamentals.py FLOW_FIELDS + STOCK_FIELDS ile ayni.
 */
export const OVERRIDABLE_FIELDS = [
	"revenue", "cost_of_revenue", "gross_profit", "operating_income",
	"net_income", "pretax_income", "tax_expense", "interest_expense",
	"sga", "rnd", "dep_amort",
	"cfo", "capex", "cfi", "cff", "sbc", "stock_issued", "dividends_paid",
	"assets", "current_assets", "liabilities", "current_liabilities",
	"equity", "cash", "short_term_investments", "long_term_debt",
	"short_term_debt", "operating_lease_current", "operating_lease_noncurrent",
	"goodwill", "intangibles", "retained_earnings", "receivables",
	"inventory", "ppe_net", "deferred_revenue", "debt_due_2y",
	"shares_diluted", "shares_basic",
] as const;

export type Ticker = z.infer<typeof tickerSchema>;

/** Bos string/dizi ALANI SILMEZ — kartta yazili olani ezmemek icin atlanir. */
export function pruneEmpty<T extends Record<string, any>>(obj: T): Partial<T> {
	const out: Record<string, any> = {};
	for (const [k, v] of Object.entries(obj)) {
		if (v === undefined || v === null) continue;
		if (typeof v === "string" && v.trim() === "") continue;
		if (Array.isArray(v) && v.length === 0) continue;
		if (typeof v === "object" && !Array.isArray(v)) {
			const nested = pruneEmpty(v);
			if (Object.keys(nested).length === 0) continue;
			out[k] = nested;
			continue;
		}
		out[k] = v;
	}
	return out as Partial<T>;
}

export function today(): string {
	return new Date().toISOString().slice(0, 10);
}
