from math import log, exp


class HypergeometricTest:

    def _gammaln(self, x):
        cof = [76.18009173, -86.50532033, 24.01409822, -1.231739516, 0.120858003e-2, -0.536382e-5]

        if x==0 or x==1:
            return 0

        y = x-1
        tmp = y + 5.5
        tmp -= (y+0.5)*log(tmp)
        ser = 1
        for i in range(0, 6):
            y+=1
            ser += cof[i]/y

        return log(x) + (log(2.50662827465*ser)-tmp)

    def _choose(self, A, B):
        return self._gammaln(A) - (self._gammaln(B) + self._gammaln(A-B))

    def _hypergeom(self, N, M, k, x):
        pvalue = 0

        for i in range(x, (min(k, M)+1)):
            lprob = self._choose(M, x) + self._choose((N-M), (k-i)) - self._choose(N, k)
            pvalue += exp(lprob)

        return pvalue

    def run(self, N, M, k, x):
        if not N or not M or not k or not x:
            return 1

        return self._hypergeom(N, M, k, x)
