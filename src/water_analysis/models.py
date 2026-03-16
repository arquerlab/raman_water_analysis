import numpy as np

def mult_gaussian(x, *params):
    gaussians = np.zeros_like(x)
    for i in range(0, len(params), 3):
        pos = params[i]
        amp = params[i+1]
        fwhm = params[i+2]
        gaussians = gaussians + amp * np.exp(-(np.power(x-pos,2)/(fwhm*fwhm/4.0/np.log(2.0))))
    return gaussians
    
def mult_gaussian_with_linear_background(x, *params):
    background = params[0] + params[1] * x  
    gaussians = np.zeros_like(x)
    for i in range(2, len(params), 3):
        pos = params[i]
        amp = params[i+1]
        fwhm = params[i+2]
        gaussians = gaussians + amp * np.exp(-(np.power(x-pos,2)/(fwhm*fwhm/4.0/np.log(2.0))))
    return background + gaussians

def mult_gaussian_with_horizontal_background(x, *params):
    background = params[0]
    for i in range(1, len(params), 3):
        pos = params[i]
        amp = params[i+1]
        fwhm = params[i+2]
        background = background + amp * np.exp(-(np.power(x-pos,2)/(fwhm*fwhm/4.0/np.log(2.0))))
    return background

def gaussian(x, *params):
    pos = params[0]
    amp = params[1]
    fwhm = params[2]
    return amp * np.exp(-(np.power(x-pos,2)/(fwhm*fwhm/4.0/np.log(2.0))))