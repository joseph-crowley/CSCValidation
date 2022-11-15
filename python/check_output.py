import subprocess

web_dir = 'root://eoscms.cern.ch//store/group/dpg_csc/comm_csc/cscval/www'

def check_local(IMGDIR='.', reference=[]):
    imgs = subprocess.check_output(f'ls {IMGDIR}/*.png | xargs basename', shell=True).decode('ascii').split('\n')[:-1]
    #print(f'this run is missing plots:\n{set(reference) - set(imgs)}\n')
    return set(imgs)

def check_remote(IMGDIR=web_dir+'/results/run356428/Muon-ZMu/Site/PNGS',use_proxy=False, reference=[]):
    # get a voms proxy
    if not use_proxy:
        import getVOMSProxy as voms
        X509_USER_PROXY, username = voms.getVOMSProxy()
        use_proxy = f'env -i X509_USER_PROXY={X509_USER_PROXY}'

    # check remote location
    imgs = subprocess.check_output(f'{use_proxy} gfal-ls {IMGDIR} | grep png', shell=True).decode('ascii').split('\n')[:-1]
    #print(f'this run is missing plots:\n{set(reference) - set(imgs)}\n')
    print(f'ref: {len(reference)}, loc: {len(imgs)}\n\n')
    print(f'images not in ref: {set(imgs) - set(reference)}, loc: {set(reference) - set(imgs)}\n\n')
    for ref,loc in zip(sorted(set(reference)),sorted(set(imgs))):
        print(f"{ref = }, {loc = }")
    return set(imgs)
    

def check_transfer():
    # check that local and remote are the same
    local = check_local()
    remote = check_remote()

    return local == remote

if __name__ == '__main__':
    with open('plot_list_ref.csv','r') as f:
        reference = f.read().split('\n')[:-1]

    check_local(reference=reference)
    check_remote(reference=reference)
