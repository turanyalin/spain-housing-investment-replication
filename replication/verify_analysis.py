"""Independent audit of archived regressions and exploratory time series diagnostics.

Run after analyze.py. Requires statsmodels in addition to the core dependencies.
Checks OLS and the calendar-aware HAC covariance against statsmodels, using
zero score contributions for excluded calendar years rather than closing gaps.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.sandwich_covariance import S_hac_simple
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.stattools import adfuller

ROOT=Path(__file__).resolve().parent

def main():
    results=json.loads((ROOT/'results.json').read_text())
    data=pd.read_csv(ROOT/'analysis_data.csv')
    reports={}
    for name,res in results['models'].items():
        terms=[k for k in res['coefficients'] if k!='constant']
        z=data[data.year.isin(res['years'])].copy()
        X=sm.add_constant(z[terms],has_constant='add');y=z[res['outcome']]
        fit=sm.OLS(y,X).fit()
        score=pd.DataFrame(X.to_numpy()*fit.resid.to_numpy()[:,None],index=z.year)
        score=score.reindex(range(int(z.year.min()),int(z.year.max())+1),fill_value=0).to_numpy()
        bread=fit.normalized_cov_params.to_numpy()
        cov=len(z)/res['df']*bread@S_hac_simple(score,nlags=res['hac_lags'])@bread
        target=np.array([v['beta'] for v in res['coefficients'].values()])
        target_se=np.array([v['se'] for v in res['coefficients'].values()])
        assert np.max(np.abs(fit.params.to_numpy()-target))<1e-8
        assert np.max(np.abs(np.sqrt(np.diag(cov))-target_se))<1e-8
        assert np.max(np.abs(cov-np.asarray(res['covariance'])))<1e-8
        assert abs(float(fit.rsquared)-res['r2'])<1e-10
        reports[name]={'ols_verified':True,'calendar_hac_verified':True,'full_covariance_verified':True,'n':int(len(z))}
        if name=='M3':
            reports['residual_ljung_box']=acorr_ljungbox(fit.resid,lags=[1,2],model_df=0,return_df=True).to_dict('index')
            reports['dummy_2020_leverage']=float(fit.get_influence().hat_matrix_diag.max())
    for variable in ['g_manufacturing','g_house','g_gdp']:
        v=data[variable].dropna()
        # Fixed lag 1 and an intercept; no automatic lag or trend selection.
        test=adfuller(v,maxlag=1,regression='c',autolag=None)
        reports[variable+'_ADF']={'statistic':float(test[0]),'p':float(test[1]),'lag':int(test[2]),'n':int(test[3])}
    (ROOT/'submission_statistical_checks.json').write_text(json.dumps(reports,indent=2))
    print(json.dumps(reports,indent=2))

if __name__=='__main__':main()
