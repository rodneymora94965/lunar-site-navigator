"""Elige una hora de render para las escenas 3D de los sitios 456, 1358 y 964 (no afecta las cifras de la app)."""
import subprocess, numpy as np, pandas as pd, json, sys
import os
from pathlib import Path
from horizon2 import horizon as _horizon, load_terrain
U=str(Path(os.environ.get('LUNAR_SOURCE_DIR', Path(__file__).resolve().parents[2]/'luna_polo_sur')))+os.sep
os.environ.setdefault('LOLA_DATA_DIR',U+'datos')
_T=load_terrain()
horizon=lambda x,y,h: _horizon(_T,x,y,h,naz=720)
S=pd.read_csv(U+'entrega_spaceapps/candidatos_finales.csv',encoding='utf-8-sig')
res={}
for sid in [456,1358,964]:
    r=S[S.id==sid].iloc[0]
    tag=f"{r.lat_deg:.2f}_{r.lon_east_deg:.2f}".replace('-','S').replace('.','p')
    subprocess.run([sys.executable,U+'efemerides_polo_sur.py','--lat',str(r.lat_deg),'--lon',str(r.lon_east_deg),'--start','2026-11-01','--years','10','--step-hours','1','--kernels',U+'kernels','--out','.'],capture_output=True)
    e=pd.read_csv(f'efemerides_{tag}.csv')
    azs,hz=horizon(r.x_m,r.y_m,5.0)
    hi=lambda a: np.interp(a%360,np.r_[azs,360],np.r_[hz,hz[0]])
    e['sh']=e.sol_elev_deg-hi(e.sol_az_deg); e['th']=e.tierra_elev_deg-hi(e.tierra_az_deg)
    sv=e.sh>0; tv=e.th>0
    print(sid,'sun %.1f earth %.1f both %.1f'%(100*sv.mean(),100*tv.mean(),100*(sv&tv).mean()),' (entrega: %.1f %.1f %.1f)'%(r.sun_time_pct,r.earth_time_pct,r.both_time_pct),flush=True)
    def vec(az,el):
        a=np.radians(az); l=np.radians(el); return np.c_[np.sin(a)*np.cos(l),np.cos(a)*np.cos(l),np.sin(l)]
    el_=np.degrees(np.arccos((vec(e.sol_az_deg.values,e.sol_elev_deg.values)*vec(e.tierra_az_deg.values,e.tierra_elev_deg.values)).sum(1).clip(-1,1)))
    e['elong']=el_
    c=e[(e.sh>0.15)&(e.sh<1.0)&(e.th>1.5)&(e.elong>70)&(e.elong<130)]
    print(' candidatos',len(c))
    if len(c)==0: c=e[(e.sh>0.05)&(e.th>0.5)]
    b=c.sort_values('th',ascending=False).iloc[0]; print(b.to_dict(),flush=True)
    res[sid]=dict(x=float(r.x_m),y=float(r.y_m),utc=b.utc,sun_az=float(b.sol_az_deg),sun_el=float(b.sol_elev_deg),earth_az=float(b.tierra_az_deg),earth_el=float(b.tierra_elev_deg),sh=float(b.sh),th=float(b.th),pct=[float(100*sv.mean()),float(100*tv.mean()),float(100*(sv&tv).mean())],hzmax=float(hz.max()))
json.dump(res,open('sitios.json','w'),indent=1)
