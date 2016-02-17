import numpy as N
from matplotlib import pylab as plt
from scipy import optimize


def gaussian(p, x):
    return p[0]*N.exp(-((x-p[1])**2)/(2*p[2]**2))


def residualsG(p, y, x):
    err = y-gaussian(p, x)
    return err


def gaussianFit(data, numBins, figFileName, loBound=0, hiBound=0):

    cleanL = []
    for a in data:
        if not N.isnan(a):
            cleanL.append(a)

    if hiBound == 0:
        hiB = 3*N.std(cleanL)
    else:
        hiB = hiBound

    if loBound == 0:
        loB = -hiB
    else:
        loB = loBound

    n, bins, patches = plt.hist(cleanL, bins=numBins, range=(loB, hiB))
    amp = max(n.tolist())
    mean = N.mean(cleanL)
    width = N.std(cleanL)
    p0 = [amp, mean, width]
    # get midpoint of bins to standardize length
    startL = bins.tolist()
    outL = []
    for b in range(0, len(startL)-1):
        outL.append(0.5*(startL[b]+startL[b+1]))
    xA = N.array(outL)

    # do least squares optimization
    plsq = optimize.leastsq(residualsG, p0, args=(n, xA))
    fitAmp, fitMean, fitStd = plsq[0][0], plsq[0][1], plsq[0][2]

    # plot to check
    check = gaussian(plsq[0], xA)
    plt.plot(xA, n, 'bo', hold="True", alpha=0.5)
    plt.plot(xA, check, 'r-')
    plt.savefig(figFileName)
    plt.clf()

    return fitAmp, fitMean, fitStd
