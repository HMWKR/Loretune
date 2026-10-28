from pathlib import Path
import numpy as np,json
from PIL import Image
out=Path(__file__).resolve().parent;data=out/'output';names=['native-byte-pbr','raw-float-pbr','inverse-srgb-float-pbr','raw-float-emission'];arrays={n:np.flipud(np.load(data/(n+'-linear.npy'))[:,:,:3]).astype(np.float64) for n in names};pngs={n:np.array(Image.open(data/(n+'.png')).convert('RGB')).astype(np.float64) for n in names};Y=np.array([.2126,.7152,.0722]);regions={'whole_frame':[0,0,480,270],'seat_interior':[210,145,260,165],'backrest_interior':[220,70,260,95]};reports={}
for region,(x0,y0,x1,y1) in regions.items():
 summaries={}
 for n in names:
  a=arrays[n][y0:y1,x0:x1];p=pngs[n][y0:y1,x0:x1];summaries[n]={'linear_rgb_mean':a.mean((0,1)).tolist(),'linear_Y_mean':float((a@Y).mean()),'png_rgb_mean':p.mean((0,1)).tolist()}
 pairs=[]
 for label,a,b in [('byte_to_float_bridge','native-byte-pbr','raw-float-pbr'),('A_transfer_function','raw-float-pbr','inverse-srgb-float-pbr'),('B_material_lighting','raw-float-pbr','raw-float-emission')]:
  ld=arrays[b][y0:y1,x0:x1]-arrays[a][y0:y1,x0:x1];pd=pngs[b][y0:y1,x0:x1]-pngs[a][y0:y1,x0:x1];ratio=summaries[b]['linear_Y_mean']/summaries[a]['linear_Y_mean'];pairs.append({'comparison':label,'baseline':a,'variant':b,'linear_Y_mean_ratio':ratio,'linear_Y_mean_percent_change':(ratio-1)*100,'linear_rgb_mean_difference':ld.mean((0,1)).tolist(),'png_channel_mean_difference':pd.mean((0,1)).tolist(),'png_channel_mean_absolute_difference':float(np.abs(pd).mean()),'png_channel_max_absolute_difference':float(np.abs(pd).max())})
 reports[region]={'box_png_xyxy':regions[region],'pixels':(x1-x0)*(y1-y0),'summaries':summaries,'comparisons':pairs}
record={'region_method':'Same fixed pixel boxes in allcases. Seat/backrest boxes manually selected inside visible surfaces of baselinePNG; not full object segmentation, no reference-input correspondence. Wholeframe includes background. Linear buffers flipped vertically toPNG orientation.','regions':reports,'limits':['Discarded failed automatic mask and its subject-statistics interpretation preserved in analysis-attempt-1-rejected','ROI results describe local regions only; not whole-object quality or additive causal attribution','Four samples/one seed, no convergence interval','Model training encoding remains unknown; darker is not correctness']};(out/'pixel-analysis.json').write_text(json.dumps(record,indent=2));print(json.dumps({k:v['comparisons'] for k,v in reports.items()},indent=2))
