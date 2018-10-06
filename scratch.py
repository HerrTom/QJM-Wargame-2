def linspace(val,num):
    # generates a linearly spaced vector from 0 to val
    vec = []
    for i in range(num):
        vec.append(i*val/num)
    return vec