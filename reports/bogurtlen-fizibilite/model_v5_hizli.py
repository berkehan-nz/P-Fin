"""v5 hızlı kurulum: 2. yılda tama yakın verim için kalem kalem kurulum maliyeti (10 / 20 da).

    cd reports/bogurtlen-fizibilite && python model_v5_hizli.py
"""
import sys; sys.path.insert(0,'.')
import model_v5 as v5, model_v2 as v2
FX=47
# (grup, kalem, miktar, 10 da USD, 20 da USD)
I=[
("A. Arazi hazırlığı","Toprak etüdü + analiz (2 derinlik, drenaj kontrolü)","1 set",300,500),
("A. Arazi hazırlığı","Dip kazan + diskaro + lazerli tesviye","",1150,2300),
("A. Arazi hazırlığı","Yanmış çiftlik gübresi / kompost 4 t/da","40 / 80 t",2000,4000),
("A. Arazi hazırlığı","Yüksek sedde (40 cm) yapımı","3.300 / 6.600 m",450,900),
("A. Arazi hazırlığı","Agrotekstil malç örtü","3.400 / 6.800 m²",1100,2200),
("B. Fidan","2 yaşlı saksılı sertifikalı fidan (güçlü kol), sık dikim 3 × 0,75 m","4.530 / 9.060 ad × $6,5",29445,58890),
("B. Fidan","Dikim işçiliği + başlangıç gübre/kök uyarıcı","",600,1200),
("C. Telli terbiye","Galvaniz direk 6 m aralık, 3 kat tel, T-kol, ankraj (1-2. yıl yüküne göre güçlü)","",8500,17000),
("C. Telli terbiye","%35 gölge filesi + direk uzatma (1. yıldan)","",3800,7600),
("D. Sulama","Hidrant bağlantısı, disk+kum filtre, ana hat, basınç ayarlı çift lateral","6.600 / 13.200 m",2450,4900),
("D. Sulama","Fertigasyon beyni: kendi PLC/ESP32 kontrolörün + selenoid vanalar","4 / 8 zon",900,1400),
("D. Sulama","Dozaj pompaları (2 gübre + 1 asit) + hat içi EC/pH","",2200,2200),
("E. Veri ve sensör","LoRaWAN gateway + 4G + yedek hat + solar/akü","",700,700),
("E. Veri ve sensör","DIY toprak düğümü (30/60 cm nem-EC-sıcaklık)","8 / 16 ad × $280",2240,4480),
("E. Veri ve sensör","Profesyonel referans prob (DIY kalibrasyonu)","1",900,900),
("E. Veri ve sensör","Meteoroloji istasyonu (yaprak ıslaklığı, PAR, don alarmı)","1",1600,1600),
("E. Veri ve sensör","Zon başı debimetre + basınç sensörü","4 / 8 zon",800,1600),
("E. Veri ve sensör","Hava kalitesi (PM2.5/PM10) sensörü","1",500,500),
("E. Veri ve sensör","Edge sunucu (GPU'lu mini PC) + UPS + dış ortam kabini","1",1400,1400),
("E. Veri ve sensör","Yazılım/prototip bütçesi (pano, alarm, QR izlenebilirlik)","",1000,1000),
("F. Kamera","Solar 4G PTZ AI güvenlik kamerası","2",1300,1300),
("F. Kamera","Solar termal kamera","1",1600,1600),
("F. Kamera","SWD tuzak kamerası (AI sinek sayımı)","3 / 5",450,750),
("F. Kamera","Sıra kamerası (meyve sayımı → rekolte tahmini)","4 / 6",600,900),
("G. Hasat ve soğuk zincir","40' reefer konteyner, yenilenmiş (0/+2 °C)","1",8500,8500),
("G. Hasat ve soğuk zincir","Ön soğutma tüneli (cebri hava, kendi yapımın)","1",1500,1500),
("G. Hasat ve soğuk zincir","NFC'li toplayıcı tartı istasyonu + hassas terazi + QR etiket yazıcı","1 / 2 set",1500,2400),
("G. Hasat ve soğuk zincir","Hasat kasaları, arabalar, raf, transpalet","",1600,2600),
("G. Hasat ve soğuk zincir","Soğuk zincir sıcaklık logger'ları","10",500,500),
("G. Hasat ve soğuk zincir","Gıda işletme kaydı + İyi Tarım belgesi + hijyen","",1500,1500),
("H. Enerji ve saha","Trifaze elektrik bağlantısı + pano","",3500,3500),
("H. Enerji ve saha","10 kWp GES (soğuk oda + pompa, mahsuplaşmalı)","",7500,7500),
("H. Enerji ve saha","Beton zemin + gölgelik (konteyner sahası)","60 m²",4000,4000),
("H. Enerji ve saha","Çevre çiti + 2 kapı","~450 / ~640 m",3600,5000),
("H. Enerji ve saha","Konteyner ofis + dinlenme (WC/duş, kontrol odası)","20'",6000,6000),
("H. Enerji ve saha","Alet / gübre depo konteyneri","20'",2500,2500),
("H. Enerji ve saha","İç yol, stabilize, sıra başı manevra alanı","",1200,2000),
("I. Mekanizasyon","Dar bahçe traktörü (2. el, 50-60 HP) + atomizör + sıra arası biçme","",25000,25000),
("J. Diğer","Proje, 5403 tarımsal yapı izni, ÇKS, ziraat danışmanı (1. yıl)","",1500,1500),
]
def tot(col):
    return sum(r[col] for r in I)
groups={}
for g,k,q,a,b in I:
    groups.setdefault(g,[0,0]); groups[g][0]+=a; groups[g][1]+=b
b10,b20=tot(3),tot(4)
print("| Grup | Kalem | Miktar (10 / 20 da) | 10 da USD | 20 da USD | 20 da TL |")
print("|---|---|---|---:|---:|---:|")
for g,k,q,a,b in I:
    print(f"| {g[3:]} | {k} | {q} | {v2.fmt(a)} | {v2.fmt(b)} | {v2.fmt(b*FX)} |")
c10,c20=b10*0.08,b20*0.08
print(f"| | **Ara toplam** | | **{v2.fmt(b10)}** | **{v2.fmt(b20)}** | **{v2.fmt(b20*FX)}** |")
print(f"| | Beklenmeyen giderler (%8) | | {v2.fmt(c10)} | {v2.fmt(c20)} | {v2.fmt(c20*FX)} |")
print(f"| | **KURULUM TOPLAMI** | | **{v2.fmt(b10+c10)}** | **{v2.fmt(b20+c20)}** | **{v2.fmt((b20+c20)*FX)}** |")
print()
for g,(a,b) in groups.items(): print(g, a, b, round(b/(b20)*100,1))
print('traktörsüz', b10+c10-25000*1.08, b20+c20-25000*1.08)
# hızlı verim profili: 10 da başına
Y=[3.5,15,20,20,20]
for area in (10,20):
    v5.YIELD[:]=Y
    v5.PACK_SHARE[:]=[0.7,0.8,0.8,0.8,0.8]
    r=v5.run(area)
    capex=(b10+c10) if area==10 else (b20+c20)
    extra_fixed=[1500]*5  # traktör yakıt+bakım
    wc=0
    cum=-capex; out=[]
    for i,x in enumerate(r['rows']):
        e=x['ebitda']-extra_fixed[i]-(9000 if area==10 else 0)*0  # 10 da teknisyensiz
        cash=e-x['stopaj']
        cum+=cash; out.append((x['y'],round(x['kg']/1000,1),round(x['rev']),round(e),round(cum)))
    print(area,out)
