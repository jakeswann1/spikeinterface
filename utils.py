def custom_tetrode_params():
    custom_klusta_params = {'adjacency_radius': None,
                 'threshold_strong_std_factor': 3.5,
                 'threshold_weak_std_factor': 1.5,
                 'detect_sign': -1,
                 'extract_s_before': 16,
                 'extract_s_after': 32,
                 'n_features_per_channel': 3,
                 'pca_n_waveforms_max': 10000,
                 'num_starting_clusters': 50,
                 'n_jobs': -1,
                 'total_memory': None,
                 'chunk_size': None,
                 'chunk_memory': None,
                 'chunk_duration': '1s',
                 'progress_bar': True
                } 
    return custom_klusta_params

def custom_probe_params():
    custom_klusta_params = {'adjacency_radius': None,
                 'threshold_strong_std_factor': 5,
                 'threshold_weak_std_factor': 2,
                 'detect_sign': -1,
                 'extract_s_before': 16,
                 'extract_s_after': 32,
                 'n_features_per_channel': 3,
                 'pca_n_waveforms_max': 10000,
                 'num_starting_clusters': 50,
                 'n_jobs': -1,
                 'total_memory': None,
                 'chunk_size': None,
                 'chunk_memory': None,
                 'chunk_duration': '1s',
                 'progress_bar': True
                } 
    return custom_klusta_params

def generate_tetrodes(n):
    # Returns a spikeinterface ProbeGroup object with n tetrodes spaced 300um apart vertically
    
    import numpy as np
    from probeinterface import generate_tetrode, ProbeGroup
    from probeinterface import write_prb
    
    probegroup = ProbeGroup()
    for i in range(n):
        tetrode = generate_tetrode()
        tetrode.move([0, i * 300])
        tetrode.set_device_channel_indices(np.arange(i*4, i*4+4))
        probegroup.add_probe(tetrode)
    
    
    from probeinterface.plotting import plot_probe, plot_probe_group
    plot_probe_group(probegroup, with_channel_index = True)
    return probegroup

def preprocess(recording, recording_name, base_folder, electrode_type, num_channels):
    # Adds a Probe object to a Spikeinterface recording object
    # Cuts the recording to 'num_channels' channels
    # Saves the recording to a preprocessing folder
    
    from probeinterface import read_prb
    from probeinterface.plotting import plot_probe, plot_probe_group
    from pathlib import Path
    import probeinterface.probe
    import spikeinterface as si
    
    preprocessing_folder = Path(f'{base_folder}/{recording_name}_preprocessed')

    if electrode_type == 'tetrode' or electrode_type == '8_tetrode':
#         probe = read_prb('/home/isabella/Documents/isabella/klusta_testdata/spikeinterface/8_tetrodes.prb') #Load probe
        probe = generate_tetrodes(int(num_channels/4))
        
    elif electrode_type == 'probe' or electrode_type == '32 ch four shanks':
        probe = read_prb('/home/isabella/Documents/isabella/klusta_testdata/spikeinterface/4x8_buzsaki_oneshank.prb') #Load probe
    else:
        raise ValueError('Electrode type is set wrong, please set to either "probe" or "tetrode"')

    plot_probe_group(probe, with_channel_index = True)
    #plt.savefig(f'{base_folder}/probe_layout.png')

    if (preprocessing_folder).is_dir():
        print(preprocessing_folder)
        recording = si.load_extractor(preprocessing_folder)
        print(f'32-channel {electrode_type} recording loaded from previous preprocessing')
        print(recording)
        return recording
    else:
        channel_ids = recording.get_channel_ids()
        recording = recording.channel_slice(channel_ids=channel_ids[:num_channels]) #Cut to correct number of channels

        ## Currently necessary as the probe is being treated as a single shank
        ## This turns the probe object from ProbeGroup to Probe
        if electrode_type == 'probe':
            singleProbe = probeinterface.Probe.from_dict(probe.to_dict()['probes'][0])
            recording = recording.set_probe(singleProbe)
        elif electrode_type == 'tetrode':
            recording = recording.set_probegroup(probe, group_mode='by_probe')

        recording_saved = recording.save(folder=preprocessing_folder)
        print('Recording preprocessed and saved')
        return recording
    

def sort(recording, recording_name, base_folder, electrode_type, sorting_suffix):
    # Takes a preprocessed Spikeinterface recording object, and sorts using Klusta
    
    from pathlib import Path
    import spikeinterface as si
    import spikeinterface.sorters as ss
    
#     recordings = recording.split_by(property='group', outputs='dict')
    
    if electrode_type == 'tetrode':
        sorter_params = custom_tetrode_params()
        sorter = 'klusta'
    else:
        sorter_params = custom_probe_params()
        sorter = 'klusta'
    
    sorting_path = Path(f'{base_folder}/{recording_name}_{sorting_suffix}') 
    # Can be changed if you want to hold on to multiple sorts
    

    if (sorting_path).is_dir():
        sorting = si.load_extractor(sorting_path / 'sort')
        print(f"Sorting loaded from file {sorting_path}")

    else:
        sortings = []
        if electrode_type == 'tetrode':
        # Run klusta on tetrode recording using custom_tetrode_params above
            sorting = ss.run_sorter('klusta', recording, output_folder=f'{sorting_path}',
                        verbose = True, docker_image = False, **custom_tetrode_params())
 
        elif electrode_type == 'probe' or electrode_type == '32 ch four shanks':
        # Run klusta on probe recording using custom_tetrode_params above
            sorting = ss.run_sorter('klusta', recording, output_folder=f'{sorting_path}/{group}',
                                    verbose = True, docker_image = False, **custom_probe_params())
            
        else:
            print('Tetrode type set wrong')
        
        print(f'Recording sorted!\n Klusta found {len(sorting.get_unit_ids())} units\n {recording}')
        sorting = sorting.remove_empty_units()
        sortings.append(sorting)
        sortings = si.aggregate_units(sortings)    
        print('\nSorting Complete\n', sortings)
        sortings_saved = sorting.save(folder=sorting_path / 'sort')
        print(f'Sorting saved to {sorting_path}/sort \n Klusta found {len(sorting.get_unit_ids())} units')
            


    #raster = si.widgets.plot_rasters(sorting)
    
def get_mode(set_file):
    # Gets recording mode from channel 0 in set file
    # Assumes all channels are recorded in the same mode
    
    f = open(set_file, 'r')
    mode = f.readlines()[14][10]
    return mode
    
    
