// Aethon independently authored, trusted local rasterizer. No expressions/network.
import Foundation
import CoreGraphics
import CoreText
import ImageIO
import UniformTypeIdentifiers

enum RenderError: Error { case invalid }
func color(_ value: String, _ alpha: Double = 1) throws -> CGColor {
    guard value.count == 7, value.first == "#", let hex = UInt32(value.dropFirst(), radix: 16) else { throw RenderError.invalid }
    return CGColor(red: Double((hex >> 16) & 255)/255, green: Double((hex >> 8) & 255)/255, blue: Double(hex & 255)/255, alpha: alpha)
}
func run() throws {
    guard CommandLine.arguments.count == 3, ["validate", "png"].contains(CommandLine.arguments[1]) else { throw RenderError.invalid }
    let raw = FileHandle.standardInput.readData(ofLength: 100001)
    guard raw.count <= 100000, let obj = try JSONSerialization.jsonObject(with: raw) as? [String:Any],
          (obj["width"] as? Int) == 1920, (obj["height"] as? Int) == 1080,
          let background = obj["background"] as? String, let layers = obj["layers"] as? [[String:Any]], layers.count <= 8 else { throw RenderError.invalid }
    let ctx = CGContext(data:nil,width:1920,height:1080,bitsPerComponent:8,bytesPerRow:1920*4,
        space:CGColorSpace(name:CGColorSpace.sRGB)!,bitmapInfo:CGImageAlphaInfo.premultipliedLast.rawValue | CGBitmapInfo.byteOrder32Big.rawValue)!
    ctx.setFillColor(try color(background));ctx.fill(CGRect(x:0,y:0,width:1920,height:1080))
    let fontURL = URL(fileURLWithPath:"/System/Library/Fonts/AppleSDGothicNeo.ttc")
    guard let descriptors = CTFontManagerCreateFontDescriptorsFromURL(fontURL as CFURL) as? [CTFontDescriptor],
          let desc = descriptors.first(where:{(CTFontDescriptorCopyAttribute($0,kCTFontStyleNameAttribute) as? String) == "Regular"}) else { throw RenderError.invalid }
    var evidence:[[String:Any]] = []
    for layer in layers {
        guard let kind=layer["kind"] as? String, let id=layer["id"] as? String,
              let x=layer["x"] as? Double,let y=layer["y"] as? Double,let opacity=layer["opacity"] as? Double,
              let w=layer["width"] as? Double,let h=layer["height"] as? Double,let fill=layer["color"] as? String,
              [x,y,opacity,w,h].allSatisfy({$0.isFinite}),abs(x)<=3840,abs(y)<=2160,w>0,w<=1920,h>0,h<=1080,opacity>=0,opacity<=1 else { throw RenderError.invalid }
        ctx.saveGState();ctx.setFillColor(try color(fill,opacity))
        if kind == "text" {
            guard let text=layer["text"] as? String,text.count<=80,let size=layer["font_size"] as? Double,size>=24,size<=160 else { throw RenderError.invalid }
            let font=CTFontCreateWithFontDescriptor(desc,size,nil)
            var chars=Array(text.replacingOccurrences(of:"\n",with:"").utf16),glyphs=[CGGlyph](repeating:0,count:text.replacingOccurrences(of:"\n",with:"").utf16.count)
            guard CTFontGetGlyphsForCharacters(font,&chars,&glyphs,chars.count),!glyphs.contains(0) else { throw RenderError.invalid }
            let lines=text.components(separatedBy:"\n")
            guard lines.count<=2,Double(lines.count)*size*1.3<=h else { throw RenderError.invalid }
            var bounds:[[Double]]=[]
            for (i,lineText) in lines.enumerated() {
                let attrs:[NSAttributedString.Key:Any]=[NSAttributedString.Key(kCTFontAttributeName as String):font,
                    NSAttributedString.Key(kCTForegroundColorAttributeName as String):try color(fill,opacity)]
                let line=CTLineCreateWithAttributedString(NSAttributedString(string:lineText,attributes:attrs))
                var ascent:CGFloat=0,descent:CGFloat=0
                let advance=CTLineGetTypographicBounds(line,&ascent,&descent,nil)
                guard advance<=w,ascent+descent<=size*1.3 else { throw RenderError.invalid }
                ctx.textMatrix = .identity;ctx.textPosition=CGPoint(x:x,y:1080-y-ascent-Double(i)*size*1.3)
                let b=CTLineGetImageBounds(line,ctx);bounds.append([b.minX,b.minY,b.width,b.height])
                CTLineDraw(line,ctx)
            }
            evidence.append(["id":id,"font":CTFontCopyPostScriptName(font),"glyph_count":glyphs.count,"glyph_missing":false,"bounds":bounds])
        } else if kind == "rect" {ctx.fill(CGRect(x:x,y:1080-y-h,width:w,height:h))}
        else if kind == "circle" {guard w == h else {throw RenderError.invalid};ctx.fillEllipse(in:CGRect(x:x,y:1080-y-h,width:w,height:h))}
        else {throw RenderError.invalid}
        ctx.restoreGState()
    }
    if CommandLine.arguments[1] == "png" {
        guard let image=ctx.makeImage(),let dest=CGImageDestinationCreateWithURL(URL(fileURLWithPath:CommandLine.arguments[2]) as CFURL,UTType.png.identifier as CFString,1,nil) else {throw RenderError.invalid}
        CGImageDestinationAddImage(dest,image,nil);guard CGImageDestinationFinalize(dest) else {throw RenderError.invalid}
    }
    let result:[String:Any]=["width":1920,"height":1080,"color_space":"sRGB","text":evidence]
    FileHandle.standardOutput.write(try JSONSerialization.data(withJSONObject:result,options:.sortedKeys))
}
do {try run()} catch {FileHandle.standardError.write(Data("Motion frame/font validation failed\n".utf8));exit(1)}
