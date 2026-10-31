from PIL import Image
for f in ['/mnt/data/IMG_DE22E288-B4DC-413A-9683-BA696A7F577C.jpeg','/mnt/data/IMG_AE5D228D-CEEF-4ED4-8F9D-43C88D836B0E.jpeg']:
 im=Image.open(f)
 print(f, im.size)
 display(im.rotate(90,expand=True).resize((1850,1200)))
