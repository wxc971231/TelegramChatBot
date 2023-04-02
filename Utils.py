import os
from stability_sdk import client
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation

# 状态定义
states=['init', 
        'allGood', 
        'settingChatKey', 
        'settingImgKey', 
        'settingContextLen', 
        'creatingNewHyp',
        'creatingImg']
 
# 定义状态转移
transitions = [
    {'trigger': 'getKey',               'source': 'init',               'dest': 'allGood' },
    {'trigger': 'setApiKey',            'source': 'allGood',            'dest': 'settingChatKey'},
    {'trigger': 'setApiKey',            'source': 'init',               'dest': 'settingChatKey'},
    {'trigger': 'setImgKey',            'source': 'allGood',            'dest': 'settingImgKey'},
    {'trigger': 'setConextLen',         'source': 'allGood',            'dest': 'settingContextLen'},
    {'trigger': 'newHyp',               'source': 'allGood',            'dest': 'creatingNewHyp'},
    {'trigger': 'img',                  'source': 'allGood',            'dest': 'creatingImg'},
    {'trigger': 'imgDone',              'source': 'creatingImg',        'dest': 'allGood'},
    {'trigger': 'imgFailed',            'source': 'creatingImg',        'dest': 'allGood'},
    {'trigger': 'setApiKeyCancel',      'source': 'settingChatKey',     'dest': 'allGood'},
    {'trigger': 'setApiKeyDone',        'source': 'settingChatKey',     'dest': 'allGood'},
    {'trigger': 'setImgKeyCancel',      'source': 'settingImgKey',      'dest': 'allGood'},
    {'trigger': 'setImgKeyDone',        'source': 'settingImgKey',      'dest': 'allGood'},
    {'trigger': 'setConextLenCancel',   'source': 'settingContextLen',  'dest': 'allGood'},
    {'trigger': 'setConextLenDone',     'source': 'settingContextLen',  'dest': 'allGood'},
    {'trigger': 'newHypCancel',         'source': 'creatingNewHyp',     'dest': 'allGood'},
    {'trigger': 'newHypDone',           'source': 'creatingNewHyp',     'dest': 'allGood'},
    {'trigger': 'reset',                'source': 'allGood',            'dest': 'init'}]


os.environ['STABILITY_HOST'] = 'grpc.stability.ai:443'
def gen_img(key, prompt):
    # Set up our connection to the API.
    stability_api = client.StabilityInference(
        key = key,
        verbose=True, # Print debug messages.
        engine="stable-diffusion-512-v2-1", # Set the engine to use for generation.
        # Available engines: stable-diffusion-v1 stable-diffusion-v1-5 stable-diffusion-512-v2-0 stable-diffusion-768-v2-0
        # stable-diffusion-512-v2-1 stable-diffusion-768-v2-1 stable-inpainting-v1-0 stable-inpainting-512-v2-0
    )

    # Set up our initial generation parameters.
    answers = stability_api.generate(
        prompt=prompt,
        seed=False, # If a seed is provided, the resulting generated image will be deterministic.
                        # What this means is that as long as all generation parameters remain the same, you can always recall the same image simply by generating it again.
                        # Note: This isn't quite the case for Clip Guided generations, which we'll tackle in a future example notebook.
        steps=30, # Amount of inference steps performed on image generation. Defaults to 30.
        cfg_scale=8.0, # Influences how strongly your generation is guided to match your prompt.
                    # Setting this value higher increases the strength in which it tries to match your prompt.
                    # Defaults to 7.0 if not specified.
        width=512, # Generation width, defaults to 512 if not included.
        height=512, # Generation height, defaults to 512 if not included.
        samples=1, # Number of images to generate, defaults to 1 if not included.
        sampler=generation.SAMPLER_K_DPMPP_2M # Choose which sampler we want to denoise our generation with.
                                                    # Defaults to k_dpmpp_2m if not specified. Clip Guidance only supports ancestral samplers.
                                                    # (Available Samplers: ddim, plms, k_euler, k_euler_ancestral, k_heun, k_dpm_2, k_dpm_2_ancestral, k_dpmpp_2s_ancestral, k_lms, k_dpmpp_2m)
    )
    return answers
        