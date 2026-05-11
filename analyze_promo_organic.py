#!/usr/bin/env python3
"""
SFC — Promotion & Organic Analysis  (pandas-powered)
"""
import pandas as pd
import json

CSV = "/Users/clawrs/.openclaw/workspace/2-4 月会员数据/2-4 月会员数据.csv"

print("Loading CSV...")
df = pd.read_csv(CSV, dtype={'Item Code': str, 'Store Code': str})
df['Sales'] = pd.to_numeric(df['Sales'], errors='coerce')
df = df.dropna(subset=['Item Code', 'Sales'])
df = df[df['Sales'] > 0]
df['Is On Promotion'] = df['Is On Promotion'].astype(str).str.strip()
df['Is Organic']      = df['Is Organic'].astype(str).str.strip()
df['Store Code']      = df['Store Code'].astype(str).str.strip()
df['Member Code']     = df['Member Code'].astype(str)
df['Item Code']        = df['Item Code'].astype(str)
print(f"Rows: {len(df):,}  Stores: {sorted(df['Store Code'].unique())}")

stores = sorted(df['Store Code'].unique())

# ── Overall ─────────────────────────────────────────────────────
total_rows = len(df)
org_n_all  = int((df['Is Organic']=='1').sum())
prom_n_all = int((df['Is On Promotion']=='1').sum())
all_mems   = set(df['Member Code'].unique())
org_mems   = set(df[df['Is Organic']=='1']['Member Code'].unique())
prom_mems  = set(df[df['Is On Promotion']=='1']['Member Code'].unique())

m2type = {}
for m, g in df.groupby('Member Code'):
    has_o = (g['Is Organic']=='1').any()
    has_p = (g['Is On Promotion']=='1').any()
    m2type[m] = ('both' if has_o and has_p else
                 'organic_only' if has_o else
                 'promo_only' if has_p else 'neither')
seg = {'organic_only':0,'promo_only':0,'both':0,'neither':0}
for t in m2type.values(): seg[t] += 1

def blift(p, n):
    return round((p-n)/n*100, 1) if (n and n > 0) else 0

# ── Store summary ────────────────────────────────────────────────
print("Computing store summaries...")
store_promo_data, store_organic_data = {}, {}
store_promo_rank, store_organic_rank = [], []

for s in stores:
    sg = df[df['Store Code']==s]
    tot = len(sg); p_n = int((sg['Is On Promotion']=='1').sum())
    o_n = int((sg['Is Organic']=='1').sum())
    mems = set(sg['Member Code'])
    p_m = set(sg[sg['Is On Promotion']=='1']['Member Code'])
    o_m = set(sg[sg['Is Organic']=='1']['Member Code'])

    avg_a  = sg['Sales'].mean()
    avg_pp = sg[sg['Is On Promotion']=='1']['Sales'].mean()
    avg_np = sg[sg['Is On Promotion']=='0']['Sales'].mean()
    avg_oo = sg[sg['Is Organic']=='1']['Sales'].mean()
    avg_no = sg[sg['Is Organic']=='0']['Sales'].mean()

    pd_ = store_promo_data[s] = {
        'totalLineOrders': int(tot), 'promoLineOrders': p_n,
        'promoRate': round(p_n/tot*100,1),
        'totalMembers': len(mems), 'promoMembers': len(p_m),
        'nonPromoMembers': len(mems)-len(p_m),
        'promoMemberRate': round(len(p_m)/len(mems)*100,1) if mems else 0,
        'avgBasketAll': round(avg_a,2), 'avgBasketPromo': round(avg_pp,2),
        'avgBasketNonPromo': round(avg_np,2), 'basketLift': blift(avg_pp, avg_np),
    }
    store_organic_data[s] = {
        'totalOrders': int(tot), 'organicOrders': o_n,
        'organicRate': round(o_n/tot*100,1),
        'totalMembers': len(mems), 'organicMembers': len(o_m),
        'organicMemberRate': round(len(o_m)/len(mems)*100,1) if mems else 0,
        'avgBasketOrganic': round(avg_oo,2), 'avgBasketNonOrganic': round(avg_no,2),
    }

store_promo_rank   = sorted(store_promo_data.items(), key=lambda x: x[1]['promoRate'],   reverse=True)
store_organic_rank = sorted(store_organic_data.items(), key=lambda x: x[1]['organicRate'], reverse=True)

# ── Store × Category ─────────────────────────────────────────────
print("Computing store×category...")
store_cat_promo, store_cat_organic = {}, {}
for s in stores:
    sg = df[df['Store Code']==s]
    store_cat_promo[s]   = {}
    store_cat_organic[s] = {}
    for cat, cg in sg.groupby('Category Name'):
        tot = len(cg); p_n = int((cg['Is On Promotion']=='1').sum())
        o_n = int((cg['Is Organic']=='1').sum())
        mems = set(cg['Member Code'])
        p_m  = set(cg[cg['Is On Promotion']=='1']['Member Code'])
        o_m  = set(cg[cg['Is Organic']=='1']['Member Code'])
        app_ = cg[cg['Is On Promotion']=='1']['Sales'].mean()
        anp_ = cg[cg['Is On Promotion']=='0']['Sales'].mean()
        aop_ = cg[cg['Is Organic']=='1']['Sales'].mean()
        anp_o= cg[cg['Is Organic']=='0']['Sales'].mean()
        store_cat_promo[s][cat] = {
            'totalOrders': int(tot), 'promoOrders': p_n,
            'promoRate': round(p_n/tot*100,1),
            'members': len(mems), 'promoMembers': len(p_m),
            'promoMemberRate': round(len(p_m)/len(mems)*100,1) if mems else 0,
            'avgBasketPromo': round(app_,2), 'avgBasketNonPromo': round(anp_,2),
            'basketLift': blift(app_, anp_),
        }
        store_cat_organic[s][cat] = {
            'totalOrders': int(tot), 'organicOrders': o_n,
            'organicRate': round(o_n/tot*100,1),
            'members': len(mems), 'organicMembers': len(o_m),
            'organicMemberRate': round(len(o_m)/len(mems)*100,1) if mems else 0,
            'avgBasketOrganic': round(aop_,2), 'avgBasketNonOrganic': round(anp_o,2),
        }

# ── Store × Item ────────────────────────────────────────────────
print("Computing store×item (top 30 each)...")
store_item_promo   = {s: {} for s in stores}
store_item_organic = {s: {} for s in stores}

for s in stores:
    sg = df[df['Store Code']==s]
    for ic in sg['Item Code'].unique():
        ig = sg[sg['Item Code']==ic]
        tot = len(ig)
        p_n = int((ig['Is On Promotion']=='1').sum())
        o_n = int((ig['Is Organic']=='1').sum())
        name = ig.iloc[0]['Item Name']
        cat  = ig.iloc[0]['Category Name']
        if p_n > 0:
            avg_pp = ig[ig['Is On Promotion']=='1']['Sales'].mean()
            avg_np = ig[ig['Is On Promotion']=='0']['Sales'].mean()
            store_item_promo[s][ic] = {
                'name': name, 'cat': cat,
                'totalOrders': int(tot), 'promoOrders': p_n,
                'promoRate': round(p_n/tot*100,1),
                'avgBasketPromo': round(avg_pp,2),
                'avgBasketNonPromo': round(avg_np,2) if avg_np == avg_np else 0,  # handle NaN
                'basketLift': blift(avg_pp, avg_np),
            }
        if o_n > 0:
            store_item_organic[s][ic] = {
                'name': name, 'cat': cat,
                'totalOrders': int(tot), 'organicOrders': o_n,
                'organicRate': round(o_n/tot*100,1),
            }

for s in stores:
    top_p = sorted(store_item_promo[s].values(), key=lambda x: x['promoOrders'], reverse=True)[:30]
    top_o = sorted(store_item_organic[s].values(), key=lambda x: x['organicOrders'], reverse=True)[:30]
    # rebuild dict keyed by item code for easy lookup
    p_dict = {p['name']+'_'+p['cat']:p for p in top_p}  # use name+cat as key
    o_dict = {o['name']+'_'+o['cat']:o for o in top_o}
    # Actually key should be item code
    store_item_promo[s]   = {v['name']+'_'+v['cat']:v for v in top_p}
    store_item_organic[s] = {v['name']+'_'+v['cat']:v for v in top_o}

# Rebuild with item_code as key for cleaner HTML access
store_item_promo_k, store_item_organic_k = {}, {}
for s in stores:
    sg = df[df['Store Code']==s]
    # collect top promo
    promo_list = []
    for ic in sg['Item Code'].unique():
        ig = sg[sg['Item Code']==ic]
        tot = len(ig); p_n = int((ig['Is On Promotion']=='1').sum())
        if p_n == 0: continue
        avg_pp = ig[ig['Is On Promotion']=='1']['Sales'].mean()
        avg_np = ig[ig['Is On Promotion']=='0']['Sales'].mean()
        promo_list.append({
            'code': ic,
            'name': ig.iloc[0]['Item Name'],
            'cat': ig.iloc[0]['Category Name'],
            'totalOrders': int(tot), 'promoOrders': p_n,
            'promoRate': round(p_n/tot*100,1),
            'avgBasketPromo': round(avg_pp,2),
            'avgBasketNonPromo': round(avg_np,2) if pd.notna(avg_np) else 0,
            'basketLift': blift(avg_pp, avg_np),
        })
    promo_list.sort(key=lambda x: x['promoOrders'], reverse=True)
    store_item_promo_k[s] = {p['code']: {k:v for k,v in p.items()} for p in promo_list[:30]}

    # collect top organic
    org_list = []
    for ic in sg['Item Code'].unique():
        ig = sg[sg['Item Code']==ic]
        tot = len(ig); o_n = int((ig['Is Organic']=='1').sum())
        if o_n == 0: continue
        org_list.append({
            'code': ic,
            'name': ig.iloc[0]['Item Name'],
            'cat': ig.iloc[0]['Category Name'],
            'totalOrders': int(tot), 'organicOrders': o_n,
            'organicRate': round(o_n/tot*100,1),
        })
    org_list.sort(key=lambda x: x['organicOrders'], reverse=True)
    store_item_organic_k[s] = {o['code']: {k:v for k,v in o.items()} for o in org_list[:30]}

# ── Write ────────────────────────────────────────────────────────
out = {
    'totalMembers': len(all_mems),
    'totalLineOrders': int(total_rows),
    'organicLineOrders': org_n_all,
    'organicLineRate': round(org_n_all/total_rows*100,1),
    'promoLineOrders': prom_n_all,
    'promoLineRate': round(prom_n_all/total_rows*100,1),
    'organicMembers': len(org_mems),
    'organicMemberRate': round(len(org_mems)/len(all_mems)*100,1),
    'promoMembers': len(prom_mems),
    'promoMemberRate': round(len(prom_mems)/len(all_mems)*100,1),
    'promoStoreSummary': store_promo_data,
    'promoStoreRanking': [{'store':s,**d} for s,d in store_promo_rank],
    'promoStoreCat': store_cat_promo,
    'promoStoreItem': store_item_promo_k,
    'organicStoreSummary': store_organic_data,
    'organicStoreRanking': [{'store':s,**d} for s,d in store_organic_rank],
    'organicStoreCat': store_cat_organic,
    'organicStoreItem': store_item_organic_k,
    'memberSegmentation': seg,
}

out_path = "/Users/clawrs/.openclaw/workspace/2-4 月会员数据/promo_organic_data.js"
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(f"var PROMO_ORGANIC_DATA = {json.dumps(out, ensure_ascii=False, indent=2)};")
print(f"\n✅ Written → {out_path}")

print("\n── Promo Store Ranking ──")
for s,d in store_promo_rank: print(f"  Store {s}: {d['promoRate']}% lines promo, lift={d['basketLift']}%")
print("\n── Organic Store Ranking ──")
for s,d in store_organic_rank: print(f"  Store {s}: {d['organicRate']}% lines organic, {d['organicMembers']} members")
print("\n── Member Segmentation ──")
tot = sum(seg.values())
for k,v in seg.items(): print(f"  {k}: {v} ({round(v/tot*100,1)}%)")
