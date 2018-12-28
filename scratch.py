from PIL import Image
import numpy as np
radius = 0.5
size = 100
x,y = np.meshgrid(np.linspace(-1,1,size),np.linspace(-1,1,size))
f = np.vectorize(lambda x,y: ( 1.0 if x*x + y*y < radius*radius else 0.0))
z = f(x,y)
print(z)
zz = np.random.random((size,size))
img = Image.fromarray(zz,mode='L') #replace z with zz and it will just produce a black image
img.show()

imgz = Image.fromarray((z*255).astype('uint8'))
imgz.show()