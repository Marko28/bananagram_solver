import random
import collections
import urllib.request
import copy
import asyncio 

from pyodide.http import open_url
from pyscript import document
from pyscript import display

def get_words(cL):
    target_url = "https://raw.githubusercontent.com/Marko28/bananagram_solver/main/words.txt"
    data = open_url(target_url)
    allWords = []
    for line in data:
        w = ''.join([c.upper() for c in line if c.isalpha()])
        if len(w) < 3:
            continue
        allWords.append(w)
    W, cW = [], []
    sL = set(cL)
    sW = set()
    for w in allWords:
        w = w.strip()
        cw = list(w)
        cw = collections.Counter(cw)
        if cw <= cL:
            W.append(w)
            sW.update(set(cw))
            cW.append(cw.copy())

    WcW = list(zip(W, cW))
    random.shuffle(WcW)
    
    return WcW, sW==sL

def add_first_word(w, n_g, cL):
    n_w = len(w)
    G = [[' ' for i in range(n_g)] for j in range(n_g)]
    doesFit = False
    I = [i for i in range(2*n_g**2)]
    random.shuffle(I)
    while I:
        i = I.pop()
        dir = 0
        if i >= n_g**2:
            dir = 1
            i -= n_g**2
        (i_r, i_c) = divmod(i, n_g)
        if dir and i_r + n_w >= n_g:
            continue
        if (not dir) and i_c + n_w >= n_g:
            continue
        doesFit = True
        break
    if not doesFit:
        return False, False, False
    if dir:
        for i in range(n_w):
            G[i_r+i][i_c] = w[i]
    else:
        for i in range(n_w):
            G[i_r][i_c+i] = w[i]
    cL -= collections.Counter(w)
    return G, cL, I
async def add_another_word(WcW, G, cL, I, output2_div):
    random.shuffle(WcW)
    W, cW = zip(*WcW)
    WcW2 = copy.deepcopy(WcW)
    sL = set(cL)
    for i in range(len(WcW2)-1, -1, -1):
        sW = set(WcW2[i][0])
        if sW.isdisjoint(sL):
            del WcW2[i]
    
    G2 = copy.deepcopy(G)
    cL2 = cL.copy()
    I2 = I.copy()
    random.shuffle(I2)
    n_g = len(G2)
    doesFit = False

    D = [[set("Q"),18], [set("JKXZ"),18], [set("BCFHMPVWY"),13], [set("G"),12],\
        [set("L"),11],[set("DSU"),9],[set("N"),8]]
    d = set()
    sL = set(cL2)
    
    while I2:
        j = I2.pop()
        dir = 0
        if j >= n_g**2:
            dir = 1
            j -= n_g**2
        (i_r, i_c) = divmod(j, n_g)
        if (dir and i_r != 0 and G2[i_r-1][i_c] != ' ') or ((not dir) and i_c != 0 and G[i_r][i_c-1] != ' '):
            continue
        V, i_v = [], []
        if dir:
            for i in range(i_r, n_g):
                if G2[i][i_c] == ' ':
                    continue
                V.append(G2[i][i_c])
                i_v.append(i-i_r)
        else:
            for i in range(i_c, n_g):
                if G2[i_r][i] == ' ':
                    continue
                V.append(G2[i_r][i])
                i_v.append(i-i_c)
        if not V:
            continue
        cV = collections.Counter(V)
        S = []
        min_v = 0
        for i in range(len(i_v)):
            if i_v[i] == i:
                min_v = i
            else:
                break
        for wcw in WcW2:
            w, cW = wcw[0], wcw[1]
            if len(w) <= min_v+1:
                continue
            if not cV <= cW:
                continue
            isValid = True
            for i in range(len(V)):
                if i_v[i] >= len(w):
                    isValid = False
                    break
                if w[i_v[i]] != V[i]:
                    isValid = False
                    break
            if not isValid:
                continue
            if dir and i_r + len(w) >= n_g:
                continue
            elif (not dir) and i_c + len(w) >= n_g:
                continue
            if cW - cV <= cL2:
                S.append(w)
        if not S:
            continue
        random.shuffle(S)

        for I_D in D:
            d.update(I_D[0])
            isRareWord = False
            if d.isdisjoint(sL):
                continue
            for _ in range(I_D[1]):
                w = S[0]
                if not d.isdisjoint(set(w)):
                    isRareWord = True
                    break
                random.shuffle(S)
            if isRareWord:
                break
        
        if len(S) > 1:
            S = S[:1]
        for w in S:
            G3 = copy.deepcopy(G2)
            cL3 = cL2.copy()
            if dir:
                for i in range(len(w)):
                    if G3[i_r+i][i_c] != ' ':
                        cL3.subtract(G3[i_r+i][i_c])
                    G3[i_r+i][i_c] = w[i]
            else:
                for i in range(len(w)):
                    if G3[i_r][i_c+i] != ' ':
                        cL3.subtract(G3[i_r][i_c+i])
                    G3[i_r][i_c+i] = w[i]
            cL3 -= collections.Counter(w)
            
            await asyncio.sleep(0)
            S = 'Generating solution...\n\n' + printG(G3)
            output2_div.innerText = S
            output2_div.innerText += '\n\nRemaining letters: ' + str(dict(cL3))

            if not cL3:
                if checkG(G3, W):
                    
                    return G3, cL3
                else:
                    continue

            if not checkG(G3, W):
                break
            
            G3, cL3 = await add_another_word(WcW, G3, cL3, I2, output2_div)
            if G3 is not False:
                return G3, cL3
                
    return False, False

def checkG(G, W):
    n_g = len(G)
    s_r = ''
    s_c = ''
    for i in range(n_g):
        for j in range(n_g):
            if G[i][j] == ' ':
                if len(s_c) == 0 or len(s_c) == 1:
                    pass
                elif len(s_c) == 2:
                    return False
                else:
                    if s_c not in W:
                        return False
                s_c = ''
            else:
                s_c += G[i][j]
            if G[j][i] == ' ':
                if len(s_r) == 0 or len(s_r) == 1:
                    pass
                elif len(s_r) == 2:
                    return False
                else:
                    if s_r not in W:
                        return False
                s_r = ''
            else:
                s_r += G[j][i]
    if len(s_c) == 0 or len(s_c) == 1:
        pass
    elif len(s_c) == 2:
        return False
    else:
        if s_c not in W:
            return False
    if len(s_r) == 0 or len(s_r) == 1:
        pass
    elif len(s_r) == 2:
        return False
    else:
        if s_r not in W:
            return False
    return True
def printG(G):
    I = []
    G2 = copy.deepcopy(G)
    N = len(G2)
    for i in range(N):
        isEmpty = True
        for j in range(N):
            if G2[i][j] != ' ':
                isEmpty = False
                break
        if isEmpty:
            I.append(i)
    for i in I[::-1]:
        del G2[i]

    N2 = len(G2[0])
    I = []
    for j in range(N2):
        isEmpty = True
        for i in range(len(G2)):
            if G2[i][j] != ' ':
                isEmpty = False
                break
        if isEmpty:
            I.append(j)
    S = ''
    for i in range(len(G2)):
        for j in I[::-1]:
            del G2[i][j]
        M = ['-' if x==' ' else x for x in G2[i]]
        S += ''.join(M) + '\n'
    return S

def generate_letters(event):
    nL = 144
    D = ["J", "K", "Q", "X", "Z"] * 2 + \
    ["B", "C", "F", "H", "M", "P", "V", "W", "Y"] * 3 + \
    ["G"] * 4 + ["L"] * 5 + ["D", "S", "U"] * 6 + \
    ["N"] * 8 + ["T", "R"] * 9 + ["O"] * 11 + \
    ["I"] * 12 + ["A"] * 13 + ["E"] * 18

    L = random.sample(D, nL)
    L.sort()
    textbox = document.querySelector("#letters")
    textbox.value = ''.join(L)
    
    cL = collections.Counter(L)
    output1_div = document.querySelector("#output1")
    output1_div.innerText = ', '.join(L)
    output1_div.innerText += '\n'
    output1_div.innerText += str(dict(cL))
    output1_div.innerText += f'\nTotal number of letters: {len(L)}'

async def generate_solution(event):
    textbox = document.querySelector("#letters")
    if not textbox.value:
        generate_letters(event)
    L1 = textbox.value
    L = []
    for i in L1:
        if i.isalpha():
            L.append(i.upper())
    L.sort()
    textbox.value = ''.join(L)
    
    cL = collections.Counter(L)
    output1_div = document.querySelector("#output1")
    output1_div.innerText = ', '.join(L)
    output1_div.innerText += '\n'
    output1_div.innerText += str(dict(cL))
    output1_div.innerText += f'\nTotal number of letters: {len(L)}'

    await asyncio.sleep(0)
    output2_div = document.querySelector("#output2")
    output2_div.innerText = 'Generating solution...'
    WcW, isPossible = get_words(cL)

    if not isPossible:
        output2_div.innerText = 'No solution exists.'
    
    W, cW = zip(*WcW)

    D = [[set("Q"),18], [set("JKXZ"),18], [set("BCFHMPVWY"),13], [set("G"),12],\
        [set("L"),11],[set("DSU"),9],[set("N"),8]]
    d = set()
    n_g = 20
    CL = cL.copy()
    while True:
        cL = CL.copy()
        sL = set(cL)
        for I_D in D:
            d.update(I_D[0])
            isRareWord = False
            if d.isdisjoint(sL):
                continue
            for _ in range(I_D[1]):
                w = WcW[0][0]
                if not d.isdisjoint(set(w)):
                    isRareWord = True
                    break
                random.shuffle(WcW)
            if isRareWord:
                break
                
        G, cL, I = add_first_word(w, n_g, cL)
        if G is False:
            n_g += 1
            continue
        S = 'Generating solution...\n\n' + printG(G)
        await asyncio.sleep(0)
        output2_div.innerText = S
        output2_div.innerText += '\n\nRemaining letters: ' + str(dict(cL))
        hasSol = False
        while True:
            G, cL = await add_another_word(WcW, G, cL, I, output2_div)
            if G is False:
                n_g += 1
                break
            if not cL:
                hasSol = True
                break
            await asyncio.sleep(0)
            S = 'Generating solution...\n\n' + printG(G)
            output2_div.innerText = S
            output2_div.innerText += '\n\nRemaining letters: ' + str(dict(cL))
        if hasSol:
            if not checkG(G, W):
                n_g + 1
                continue
            break
            
    await asyncio.sleep(1)
    S = 'Solution found.\n\n' + printG(G)
    output2_div.innerText = S