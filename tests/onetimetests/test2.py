from datetime import datetime

with open('brancol_usb_files') as f:
    for l in f.readlines():
            l = l.strip()
            if l.find(' ') < 0:
                 print(l[:-4])
                 continue
            n = l.split(' ')[-1]
            # print(n)
            # continue
            try:
                (_, c, r) = l.split("_")
                fd = r.split(".")[0]
                d = datetime.strptime(fd, "%d-%m-%Y-%H-%M").strftime("%Y%m%dT%H%M%SZ")
                print(d+"_"+c)
            except:
                continue