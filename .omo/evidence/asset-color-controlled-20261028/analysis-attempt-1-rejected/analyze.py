from pathlib import Path
import numpy as np,json,hashlib
from PIL import Image
out=Path(__file__).resolve().parent;data=out/'output';names=['native-byte-pbr','raw-float-pbr','inverse-srgb-float-pbr','raw-float-emission'];arrays={n:np.load(data/(n+'-linear.npy'))[:,:,:3].astype(np.float64) for n in names};pngs={n:np.array(Image.open(data/(n+'.png')).convert('RGB')).astype(np.float64) for n in names}
baseline=arrays['raw-float-pbr'];bg=baseline[0,0];mask=np.max(np.abs(baseline-bg),axis=-1)>1e-5
# Exclude antialiased silhouette: require a 3x3 neighborhood within the same subject proxy.
inner=mask.copy()
for y in [-1,0,1]:
 for x in [-1,0,1]:inner &= np.roll(np.roll(mask,y,axis=0),x,axis=1)
inner[[0,-1],:]=False;inner[:,[0,-1]]=False
assert inner.any();np.save(data/'subject-interior-mask.npy',inner);Image.fromarray((np.flipud(inner)*255).astype('uint8')).save(data/'subject-interior-mask.png')
yweights=np.array([.2126,.7152,.0722]);pngmask=np.flipud(inner);summary={}
for n in names:
 linear=arrays[n][inner];pix=pngs[n][pngmask];summary[n]={'subject_linear_rgb_mean':linear.mean(0).tolist(),'subject_linear_Y_mean':float((linear@yweights).mean()),'subject_png_rgb_mean':pix.mean(0).tolist(),'subject_png_median':np.median(pix,axis=0).tolist(),'linear_center':arrays[n][135,240].tolist(),'png_center':pngs[n][135,240].tolist()}
comparisons=[]
for label,a,b in [('byte_to_float_bridge','native-byte-pbr','raw-float-pbr'),('A_transfer_function','raw-float-pbr','inverse-srgb-float-pbr'),('B_material_lighting','raw-float-pbr','raw-float-emission')]:
 linear_diff=arrays[b][inner]-arrays[a][inner];pixdiff=pngs[b][pngmask]-pngs[a][pngmask];ratio=summary[b]['subject_linear_Y_mean']/summary[a]['subject_linear_Y_mean'];comparisons.append({'comparison':label,'baseline':a,'variant':b,'linear_Y_mean_ratio':ratio,'linear_Y_mean_percent_change':(ratio-1)*100,'linear_rgb_mean_difference':linear_diff.mean(0).tolist(),'png_channel_mean_difference':pixdiff.mean(0).tolist(),'png_channel_mean_absolute_difference':float(np.abs(pixdiff).mean()),'png_channel_max_absolute_difference':float(np.abs(pixdiff).max())})
record={'mask_rule':'Fixed baseline scene-linear pixels differing from corner background by>1e-5, eroded3x3; heuristic subject interior proxy, not ground-truth material ID. Same mask allcases. NPY/EXR bottom-up flipped to PNG orientation.','background_linear':bg.tolist(),'mask_pixel_count':int(inner.sum()),'total_pixel_count':int(inner.size),'summaries':summary,'comparisons':comparisons,'interpretation_limits':['Pairwise sensitivity under these fixed settings; not additive contribution percentages to original input difference','No training-output encoding ground truth; darkening is not correctness','Four samples per pixel, one deterministic seed; no convergence/noise confidence intervals']};(out/'pixel-analysis.json').write_text(json.dumps(record,indent=2));print(json.dumps(record,indent=2))
