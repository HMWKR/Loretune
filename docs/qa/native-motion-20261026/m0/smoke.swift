import Foundation
import CoreGraphics
import CoreText
import ImageIO
import UniformTypeIdentifiers
let width = 1920, height = 1080
let fontURL = URL(fileURLWithPath: "/System/Library/Fonts/AppleSDGothicNeo.ttc")
let descriptors = CTFontManagerCreateFontDescriptorsFromURL(fontURL as CFURL) as! [CTFontDescriptor]
let desc = descriptors.first { (CTFontDescriptorCopyAttribute($0, kCTFontStyleNameAttribute) as? String) == "Regular" }!
let font = CTFontCreateWithFontDescriptor(desc, 96, nil)
let content = "새로운 리듬"
var chars = Array(content.utf16), glyphs = [CGGlyph](repeating: 0, count: content.utf16.count)
guard CTFontGetGlyphsForCharacters(font, &chars, &glyphs, chars.count), !glyphs.contains(0) else { fatalError("Missing glyph") }
let color = CGColor(red: 0.95, green: 0.95, blue: 0.94, alpha: 1)
let attrs: [NSAttributedString.Key: Any] = [NSAttributedString.Key(kCTFontAttributeName as String): font, NSAttributedString.Key(kCTForegroundColorAttributeName as String): color]
let line = CTLineCreateWithAttributedString(NSAttributedString(string: content, attributes: attrs))
let ctx = CGContext(data: nil, width: width, height: height, bitsPerComponent: 8, bytesPerRow: width*4, space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue | CGBitmapInfo.byteOrder32Big.rawValue)!
ctx.setFillColor(CGColor(red: 0.063, green: 0.063, blue: 0.063, alpha: 1)); ctx.fill(CGRect(x: 0,y: 0,width: width,height: height))
ctx.setFillColor(CGColor(red: 0.7,green: 0.8,blue: 1,alpha: 1));ctx.fill(CGRect(x: 240,y: 200,width: 400,height: 160))
ctx.setFillColor(CGColor(red: 1,green: 0.7,blue: 0.6,alpha: 1));ctx.fillEllipse(in: CGRect(x: 1200,y: 200,width: 200,height: 200))
ctx.textPosition = CGPoint(x: 240,y: 700);CTLineDraw(line,ctx)
let image = ctx.makeImage()!
let out=URL(fileURLWithPath: CommandLine.arguments[1])
let dest=CGImageDestinationCreateWithURL(out as CFURL,UTType.png.identifier as CFString,1,nil)!
CGImageDestinationAddImage(dest,image,nil)
guard CGImageDestinationFinalize(dest) else {fatalError("PNG write failed")}
let bounds=CTLineGetImageBounds(line,ctx)
let result:[String:Any] = ["font":CTFontCopyPostScriptName(font),"glyphs":glyphs.map{Int($0)},"width":width,"height":height,"text_bounds":[bounds.origin.x,bounds.origin.y,bounds.width,bounds.height]]
print(String(data:try JSONSerialization.data(withJSONObject:result,options:.sortedKeys),encoding:.utf8)!)
