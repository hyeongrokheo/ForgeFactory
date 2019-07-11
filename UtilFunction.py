Debug_mode = True

def nPrint(obj, pList = []):
    if isinstance(obj, list):
        for o in obj:
            nPrint(o)
    else:
        print('id :', obj['id'], end='\t/\t')
        for d in pList:
            print(d, ':', obj['properties'][d], end='\t/\t')
        #if len(pList) != 0:
        print('')