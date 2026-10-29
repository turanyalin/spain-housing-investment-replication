"""Reproduce the public-data analysis. Run from this directory with Python 3.

Requires numpy, pandas, scipy and matplotlib. Raw source responses are archived.
No synthetic observations or interpolation are used.
"""
from pathlib import Path
import json, hashlib
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent

def series(file, **selection):
    d = json.loads((ROOT/file).read_text())
    dims = d['id']
    categories = {k: d['dimension'][k]['category']['index'] for k in dims}
    result, flags = {}, {}
    for year in categories['time']:
        indexes = []
        for k in dims:
            choice = year if k == 'time' else selection.get(k)
            if choice is None:
                assert len(categories[k]) == 1, (file, k)
                choice = next(iter(categories[k]))
            indexes.append(categories[k][choice])
        index = str(np.ravel_multi_index(indexes, d['size']))
        result[int(year)] = d['value'].get(index, np.nan)
        flags[int(year)] = d.get('status', {}).get(index, '')
    return pd.Series(result, dtype=float), flags

def ols_hac(data, outcome, names, lag=1):
    z = data[['year', outcome] + names].dropna()
    x = np.column_stack([np.ones(len(z)), z[names].to_numpy(float)])
    y = z[outcome].to_numpy(float)
    n,k = x.shape
    assert np.linalg.matrix_rank(x)==k and n>k
    b = np.linalg.lstsq(x,y,rcond=None)[0]
    u = y-x@b
    inv = np.linalg.inv(x.T@x)
    xu = x*u[:,None]
    # Newey-West Bartlett HAC, finite-sample n/(n-k) correction.
    # The year-distance condition preserves calendar gaps in exclusion samples.
    meat = xu.T@xu
    years = z.year.to_numpy(int)
    for h in range(1,lag+1):
        s = np.zeros((k,k))
        for i in range(n):
            for j in range(i):
                if years[i]-years[j] == h:
                    s += np.outer(xu[i],xu[j])
        meat += (1-h/(lag+1))*(s+s.T)
    cov = n/(n-k) * inv@meat@inv
    se = np.sqrt(np.diag(cov))
    t = b/se
    p = 2*stats.t.sf(np.abs(t),n-k)
    q = stats.t.ppf(.975,n-k)
    r2=1-u@u/np.sum((y-y.mean())**2)
    return dict(covariance=cov.tolist(),n=n,df=n-k,r2=float(r2),adj_r2=float(1-(1-r2)*(n-1)/(n-k)),
                year_start=int(z.year.min()),year_end=int(z.year.max()),years=z.year.tolist(),
                outcome=outcome,hac_lags=lag,dw=float(np.sum(np.diff(u)**2)/(u@u)),
                coefficients={name:dict(beta=float(bb),se=float(ss),p=float(pp),lo=float(bb-q*ss),hi=float(bb+q*ss)) for name,bb,ss,pp in zip(['constant']+names,b,se,p)},
                residuals=u.tolist(),fitted=(x@b).tolist())

def main():
    d=pd.DataFrame(index=range(1995,2025)); flags={}
    for name,asset in [('manufacturing','N11G'),('equipment','N11MG'),('ipp','N117G')]:
        d[name],flags[name]=series('manufacturing_raw.json',unit='CLV20_MEUR',asset10=asset)
    d['gdp'],flags['gdp']=series('gdp_raw.json',unit='CLV20_MEUR')
    d['dwelling'],flags['dwelling']=series('investment_raw.json',unit='CLV20_MEUR',asset10='N111G')
    h=pd.read_csv(ROOT/'house_raw.csv',parse_dates=['observation_date'])
    h['year']=h.observation_date.dt.year
    annual=h.groupby('year')['QESR628BIS'].agg(['mean','count'])
    assert (annual.loc[1995:2024,'count']==4).all()
    d['house']=annual['mean']
    assert d.notna().all().all() and (d>0).all().all()
    for col in d.columns.tolist(): d['g_'+col]=100*np.log(d[col]).diff()
    d['lag_house']=d.g_house.shift(1)
    d['lag_manufacturing']=d.g_manufacturing.shift(1)
    d['covid']=(d.index==2020).astype(int)
    d['year']=d.index
    d.to_csv(ROOT/'analysis_data.csv',index=False,float_format='%.10f')
    a=d[d.year>=1996]
    specs={
      'M1':(a,'g_manufacturing',['g_house'],1),
      'M2':(a,'g_manufacturing',['g_house','g_gdp'],1),
      'M3':(a,'g_manufacturing',['g_house','g_gdp','covid'],1),
      'M4':(a,'g_manufacturing',['g_house','g_gdp','covid','lag_house'],1),
      'R1_equipment':(a,'g_equipment',['g_house','g_gdp','covid'],1),
      'R2_ipp':(a,'g_ipp',['g_house','g_gdp','covid'],1),
      'R3_pre2008':(a[a.year<=2007],'g_manufacturing',['g_house','g_gdp'],1),
      'R4_exclude_covid':(a[~a.year.isin([2020,2021])],'g_manufacturing',['g_house','g_gdp'],1),
      'R5_hac2':(a,'g_manufacturing',['g_house','g_gdp','covid'],2),
      'R6_AR1':(a,'g_manufacturing',['g_house','g_gdp','covid','lag_manufacturing'],1),
      'R7_to2023':(a[a.year<=2023],'g_manufacturing',['g_house','g_gdp','covid'],1),
      'R8_pre2008_omit2000':(a[(a.year<=2007)&(a.year!=2000)],'g_manufacturing',['g_house','g_gdp'],1),
      'R9_boom_only':(a[(a.year>=2001)&(a.year<=2007)],'g_manufacturing',['g_house','g_gdp'],1),
    }
    results={key:ols_hac(*args) for key,args in specs.items()}
    # Leave-one-year-out sensitivity of M3, retain chronological gaps in HAC.
    loo={int(y):ols_hac(a[a.year!=y],'g_manufacturing',['g_house','g_gdp','covid'],1)['coefficients']['g_house']['beta'] for y in a.year if y!=2020}
    # Omitting the sole COVID year makes the dummy constant; refit without it.
    loo[2020]=ols_hac(a[a.year!=2020],'g_manufacturing',['g_house','g_gdp'],1)['coefficients']['g_house']['beta']
    summaries={c:dict(mean=float(a[c].mean()),sd=float(a[c].std()),minimum=float(a[c].min()),maximum=float(a[c].max()),n=int(a[c].notna().sum())) for c in ['g_manufacturing','g_house','g_gdp','g_equipment','g_ipp']}
    phases={}
    for name,lo,hi in [('early',2001,2003),('late',2004,2007),('bust',2008,2013),('recovery',2014,2019),('recent',2020,2024)]:
        phases[name]={'years':f'{lo}-{hi}',**{c:float(d.loc[lo:hi,c].mean()) for c in ['g_manufacturing','g_house','g_gdp']}}
    status={k:{str(y):f for y,f in v.items() if f} for k,v in flags.items()}
    out=dict(models=results,summary=summaries,phases=phases,status=status,loo=loo,
             correlation=float(a.g_house.corr(a.g_manufacturing)),
             growth_2000_2007={c:float(100*(d.loc[2007,c]/d.loc[2000,c]-1)) for c in ['manufacturing','house','gdp','equipment','ipp']})
    (ROOT/'results.json').write_text(json.dumps(out,indent=2))
    flat=[]
    for model,res in results.items():
        for term,values in res['coefficients'].items():flat.append(dict(model=model,term=term,n=res['n'],r2=res['r2'],hac_lags=res['hac_lags'],**values))
    pd.DataFrame(flat).to_csv(ROOT/'regression_results.csv',index=False)
    (ROOT/'summary_statistics.csv').write_text(pd.DataFrame(summaries).T.to_csv())
    plt.rcParams.update({'font.family':'DejaVu Serif','font.size':10,'pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
    fig,axs=plt.subplots(2,1,figsize=(7.2,6.0),sharex=True,gridspec_kw={'height_ratios':[1.15,1]})
    colors={'house':'#4c667f','manufacturing':'#171717','equipment':'#777777'}
    for c,label in [('house','Real house prices'),('manufacturing','Manufacturing investment'),('equipment','Manufacturing equipment investment')]:axs[0].plot(d.year,100*d[c]/d.loc[2000,c],label=label,color=colors[c],lw=1.8,ls='--' if c=='equipment' else '-')
    axs[0].set_ylabel('Index 2000 = 100');axs[0].legend(frameon=False,fontsize=8,loc='upper left')
    axs[1].plot(d.year,d.g_house,color=colors['house'],label='House prices',lw=1.6)
    axs[1].plot(d.year,d.g_manufacturing,color=colors['manufacturing'],label='Manufacturing investment',lw=1.6)
    axs[1].axhline(0,color='#999999',lw=.6);axs[1].set_ylabel('Annual log growth × 100');axs[1].legend(frameon=False,fontsize=8)
    for ax in axs:
        ax.axvspan(2000,2007,color='#c7d5e2',alpha=.3);ax.axvspan(2008,2013,color='#cccccc',alpha=.25);ax.grid(axis='y',alpha=.18)
    axs[1].set_xticks([1995,2000,2005,2010,2015,2020,2024]);fig.tight_layout()
    fig.savefig(ROOT/'figure1.png',dpi=220,bbox_inches='tight');fig.savefig(ROOT.parent/'figures'/'figure1.pdf',bbox_inches='tight');plt.close(fig)
    # Frisch-Waugh-Lovell partial relationship for baseline M3, for illustration.
    z=a.dropna(subset=['g_house','g_manufacturing','g_gdp','covid'])
    controls=np.column_stack([np.ones(len(z)),z.g_gdp,z.covid])
    def resid(v):return v-controls@np.linalg.lstsq(controls,v,rcond=None)[0]
    rx,ry=resid(z.g_house.to_numpy()),resid(z.g_manufacturing.to_numpy())
    slope=float(results['M3']['coefficients']['g_house']['beta'])
    assert abs(slope-float(rx@ry/(rx@rx)))<1e-10
    fig,ax=plt.subplots(figsize=(6.8,3.8));ax.scatter(rx,ry,c='#34495e',s=22)
    xx=np.array([min(rx)-1,max(rx)+1]);ax.plot(xx,slope*xx,color='#111111',lw=1)
    for year in [2007,2009,2012,2020,2024]:
        ix=np.flatnonzero(z.year.to_numpy()==year)[0];ax.annotate(str(year),(rx[ix],ry[ix]),xytext=(3,4),textcoords='offset points',fontsize=8)
    ax.axhline(0,color='#bbbbbb',lw=.5);ax.axvline(0,color='#bbbbbb',lw=.5)
    ax.set_xlabel('House price growth after removing GDP growth and 2020 effect')
    ax.set_ylabel('Manufacturing investment growth\nafter removing GDP growth and 2020 effect')
    ax.grid(alpha=.12);fig.tight_layout();fig.savefig(ROOT/'figure2.png',dpi=220,bbox_inches='tight');fig.savefig(ROOT.parent/'figures'/'figure2.pdf',bbox_inches='tight');plt.close(fig)
    print(json.dumps({k:{'n':v['n'],'r2':v['r2'],'house':v['coefficients']['g_house']} for k,v in results.items()},indent=2))
    print('Summaries',json.dumps(summaries));print('Phases',json.dumps(phases));print('LOO range',min(loo.values()),max(loo.values()))
    print('All data assertions and FWL coefficient check passed.')

if __name__=='__main__':main()
