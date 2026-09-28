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

/**
 * YAPILANDIRILMIS TEZ KIRICI.
 *
 * Serbest metin bir kirici ("rakip pazar payi alirsa") makine tarafindan
 * degerlendirilemez ve o yuzden hicbir zaman tetiklenmez. Yapilandirilmis
 * bicim, gunluk kosunun kart verisine bakip kendiliginden karar vermesini
 * saglar — karar anini insanin fark etmesine birakmak, sistemin varlik
 * sebebine aykiri.
 *
 * Bu SAYISAL ALAN YAZMA yasagini ihlal etmez: yasak METRIKLER ve PUANLAR
 * icindir (onlar veri hattinin isidir). Esik degeri bir tercihtir, olculen
 * bir buyukluk degil.
 */
export const breakerSchema = z.object({
	consecutive_quarters: z
		.number()
		.int()
		.min(1)
		.max(8)
		.default(2)
		.describe("Kural kac ceyrek UST USTE saglanirsa tetiklenir"),
	description: z.string().max(400).describe("Insan icin aciklama"),
	metric: z
		.string()
		.max(60)
		.describe("Kart metrigi, orn. gross_margin, roic, rev_growth_ttm"),
	op: z.enum(["<", "<=", ">", ">="]),
	value: z.number().describe("Esik deger, metrikle ayni birimde"),
});

export const assetClassSchema = z
	.enum(["STOCK", "ETF", "TL_DEPOSIT"])
	.default("STOCK");

export const sliceSchema = z
	.enum(["motor", "cekirdek_etf", "sgov", "tl"])
	.optional()
	.describe(
		"Hangi dilime yazilsin. Bos birakilirsa varlik sinifindan turetilir; " +
			"SGOV kendiliginden 'sgov' dilimine gider.",
	);

/** TL vadeli mevduat — hisse gibi 'adet x fiyat' ile degerlenmez. */
export const tlDepositSchema = z.object({
	annual_rate_pct: z.number().positive().max(200),
	bank: z.string().max(60).optional(),
	maturity_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
	principal_try: z.number().positive(),
	start_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
	usdtry_at_entry: z.number().positive(),
	withholding_pct: z.number().min(0).max(50).default(15),
	withholding_confirmed: z.boolean().default(false)
		.describe("Stopaj orani bankadan teyit edildi mi"),
});

/** Kademeli alim plani — tek seferde girmek yerine parcalara bolunmus. */
export const trancheSchema = z.object({
	amount_usd: z.number().positive(),
	date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
	done: z.boolean().default(false),
	note: z.string().max(200).default(""),
	ticker: tickerSchema.optional()
		.describe("Bos birakilirsa kaydedilen pozisyonun sembolu"),
});

/**
 * Turkiye makro girdileri (data/tr_macro.json) — ELLE girilir.
 * TL mevduat yenileme kosullari bunlardan hesaplanir. Ucretsiz ve guvenilir
 * otomatik kaynak yok; tahmini sayi yazmaktansa alani bos birakmak dogru.
 */
export const trMacroSchema = z.object({
	cpi_yoy_pct: z.number().min(0).max(200).nullable().optional()
		.describe("TUFE yillik %, son aciklanan"),
	early_election_announced: z.boolean().nullable().optional()
		.describe("Erken secim tarihi kesinlesti mi"),
	policy_rate_pct: z.number().min(0).max(200).nullable().optional()
		.describe("TCMB politika faizi %"),
	source: z.string().min(3).max(300)
		.describe("Kaynak (orn. 'TCMB 23 Eki PPK karari; TUIK Eylul TUFE'). Zorunlu."),
	tcmb_meetings: z.array(z.string().regex(/^\d{4}-\d{2}-\d{2}$/)).max(12).optional()
		.describe("PPK toplanti tarihleri (YYYY-AA-GG)"),
});

/** close_position gerekcesi ZORUNLU: neden ciktigini bilmeyen tekrarlar. */
export const closeReasonSchema = z.enum([
	"tez_kirici",
	"hedef_fiyat",
	"yeniden_dengeleme",
	"nakit_ihtiyaci",
	"tez_degisti",
]);

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
