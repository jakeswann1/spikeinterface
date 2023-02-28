def generate_tetrodes(n):
    import numpy as np
    from probeinterface import generate_tetrode, ProbeGroup
    
    probegroup = ProbeGroup()
    for i in range(n):
        tetrode = generate_tetrode()
        tetrode.move([0, i * 200])
        tetrode.set_device_channel_indices(np.arange(i*4, i*4+4))
        probegroup.add_probe(tetrode)
    
    
    from probeinterface.plotting import plot_probe, plot_probe_group
    plot_probe_group(probegroup, with_channel_index = True)
    return probegroup
