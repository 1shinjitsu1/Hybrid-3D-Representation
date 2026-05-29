#Config file to guide the execution of the provided code
# In general, the code is structured around modules (that themselves can contain modules) that get instantiated in a hierarchy as specified below
config = {
    # Input / output data locations
    'module': 'network.render.Render',
    # Model & data location
    'target_path': 'logs/fur', 'override': True,
    # Randomness seed for reproducability
    'seed': 0,
    # Dataset options
    'test_dataset_config': { 
        'module': 'network.dataset.Dataset', 
        'data_loader_config': { 
            'module': 'network.dataset.GenerateData', 
            'height': 256, 
            'width': 256, 
            'radius': 6, 
            'angle': 0.63, 
            'dataset_size': 1, 
            'pose_dist_config': { 
                'module': 'data.distribution.Sphere', 
                'sampler_config': { 
                    'module': 'data.sampler.Grid', 
                    'n': 1 
                }, 
                'u_range': (0.5, 0.5), 
                'v_range': (0.0, 0.0)
            }, 
            'parameter_dist_config': {  # Distribution of the parameters fed to the model. The position of the parameters has to match the ones from the dataset this model is trained on.
                'module': 'data.distribution.Constant', 
                'constants': [[1, 0.5, 0, -0.707, 0.707]]
                }
            }, 
            'pixel_sampler_config': { 
                'module': 'network.pixel_sampler.Full'
            }, 
            'ray_sampler_config': {
                'module': 'network.ray_sampler.Proxy',
            }, 
            'proxy_config': { 
                'module': 'network.proxy.AABB', 
                'b_0': [-10,-10,-10], #so it doesnt crop legs
                'b_1': [10,10,10] 
            }, 
            'n_epochs': 1
        },
            # Network options 
        'model_config': {  # Module specifying the network architecture, should match the one defined for training the model, n_parameters
            'module': 'network.model.ParamNerf', 
            'pos_embedding': { 
                'module': 'network.model.FourierFeatures', 
                'n_freq_bands': 10 
            }, 
            'dir_embedding': { 
                'module': 'network.model.FourierFeatures', 
                'n_freq_bands': 4 
            }, 
            'param_embedding': { 
                'module': 'network.model.FourierFeatures', 
                'n_freq_bands': 4 
            }, 
            'param_depth': 0, 
            'color_depth': 1, 
            'n_parameters': [1, 4] 
        },
            # Rendering options 
        'renderer_config': { 
            'module': 'network.renderer.InstanceRenderer', 
            'n_samples': 2048, 
            'n_importance': 0, 
            'perturb': False, 
            'raw_noise_std': 0, 
            'render_chunk': 16384, 
            'net_chunk': 32768, 
            'instancer_config': { 
                'module': 'instancer.instancer.Instancer', 
                'b_0': [-1.6, -1.6, -0.5],
                'b_1': [1.6, 1.6, 3.0], 
                'cast_shadow_rays': True, 
                'textures': ['','','light'], 
                'mesh_path': 'meshes/lion_cub.ply',
                'patch_scale': 0.05,
                'min_shadow_samples': 4,
                'n_shadow_samples': 128,
                'min_texture_samples': 4, 
                'n_texture_samples': 128,
                'jitter_amount': .3, 
                'instance_sampling_method': 'nearest_blend'
            },
            'density_reweighting': True, 
            'step_size': 0.0005 
        },
        # Logging options 
        'logger_config': { 'module': 'network.logger.Logger' 
        }
    }