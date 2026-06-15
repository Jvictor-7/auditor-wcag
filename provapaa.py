def alg(vetorA, vetorB, m, n):
    vetorC = []
    i = 0
    j = 0
    while i < m and j < n:
        if vetorA[i] < vetorB[j]:
            i += 1
        elif vetorA[i] > vetorB[j]:
            j += 1
        else: 
            vetorC.append(vetorA[i])
            i += 1
            j += 1
    return vetorC
    
vetorA = [1, 2, 3, 4, 5]
vetorB = [3, 4, 5, 6, 7]
m = len(vetorA)
n = len(vetorB)
resultado = alg(vetorA, vetorB, m, n)
print("Vetor resultado:", resultado)