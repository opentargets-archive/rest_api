from math import log, exp


class HypergeometricTest:

    def __init__(self):
        pass

    @staticmethod
    def _gammaln( x):
        cof = [76.18009173, -86.50532033, 24.01409822, -1.231739516, 0.120858003e-2, -0.536382e-5]

        if x == 0 or x == 1:
            return 0

        y = x-1
        tmp = y + 5.5
        tmp -= (y+0.5)*log(tmp)
        ser = 1
        for i, c in enumerate(cof):
            y += 1
            ser += c/y

        return log(x) + (log(2.50662827465*ser)-tmp)

    @staticmethod
    def _choose(A, B):
        return HypergeometricTest._gammaln(A) - (HypergeometricTest._gammaln(B) + HypergeometricTest._gammaln(A-B))

    @staticmethod
    def _hypergeom( N, M, k, x):
        pvalue = 0

        for i in range(x, (min(k, M)+1)):
            lprob = HypergeometricTest._choose(M, x) + HypergeometricTest._choose((N-M), (k-i)) - HypergeometricTest._choose(N, k)
            pvalue += exp(lprob)

        return pvalue

    @staticmethod
    def run( N, M, k, x):
        if not N or not M or not k or not x:
            return 1

        return HypergeometricTest._hypergeom(N, M, k, x)
