import os
import io
from PIL import Image
from stability_sdk import client
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
import aiogram
from aiogram import types
import warnings

# 状态定义
states=[
    'init', 
    'allGood', 
    'settingChatKey', 
    'settingImgKey', 
    'settingVoiceToken',
    'settingContextLen', 
    'creatingNewHyp',
    'edittingHyp',
    'deletingHyp',
    'creatingImg'
]
 
# 定义状态转移
transitions = [
    {'trigger': 'getKey',               'source': 'init',               'dest': 'allGood' },
    {'trigger': 'setApiKey',            'source': 'allGood',            'dest': 'settingChatKey'},
    {'trigger': 'setApiKey',            'source': 'init',               'dest': 'settingChatKey'},
    {'trigger': 'setImgKey',            'source': 'allGood',            'dest': 'settingImgKey'},
    {'trigger': 'setVoiceToken',        'source': 'allGood',            'dest': 'settingVoiceToken'},
    {'trigger': 'setConextLen',         'source': 'allGood',            'dest': 'settingContextLen'},
    {'trigger': 'newHyp',               'source': 'allGood',            'dest': 'creatingNewHyp'},
    {'trigger': 'editHyp',              'source': 'allGood',            'dest': 'edittingHyp'},
    {'trigger': 'delHyp',               'source': 'allGood',            'dest': 'deletingHyp'},
    {'trigger': 'img',                  'source': 'allGood',            'dest': 'creatingImg'},
    {'trigger': 'imgDone',              'source': 'creatingImg',        'dest': 'allGood'},
    {'trigger': 'imgFailed',            'source': 'creatingImg',        'dest': 'allGood'},
    {'trigger': 'setApiKeyCancel',      'source': 'settingChatKey',     'dest': 'allGood'},
    {'trigger': 'setApiKeyDone',        'source': 'settingChatKey',     'dest': 'allGood'},
    {'trigger': 'setImgKeyCancel',      'source': 'settingImgKey',      'dest': 'allGood'},
    {'trigger': 'setImgKeyDone',        'source': 'settingImgKey',      'dest': 'allGood'},
    {'trigger': 'setVoiceTokenCancel',  'source': 'settingVoiceToken',  'dest': 'allGood'},
    {'trigger': 'setVoiceTokenDone',    'source': 'settingVoiceToken',  'dest': 'allGood'},
    {'trigger': 'setConextLenCancel',   'source': 'settingContextLen',  'dest': 'allGood'},
    {'trigger': 'setConextLenDone',     'source': 'settingContextLen',  'dest': 'allGood'},
    {'trigger': 'newHypCancel',         'source': 'creatingNewHyp',     'dest': 'allGood'},
    {'trigger': 'newHypDone',           'source': 'creatingNewHyp',     'dest': 'allGood'},
    {'trigger': 'editHypCancel',        'source': 'edittingHyp',        'dest': 'allGood'},
    {'trigger': 'editHypDone',          'source': 'edittingHyp',        'dest': 'allGood'},
    {'trigger': 'delHypCancel',         'source': 'deletingHyp',        'dest': 'allGood'},
    {'trigger': 'delHypDone',           'source': 'deletingHyp',        'dest': 'allGood'},
    {'trigger': 'reset',                'source': 'allGood',            'dest': 'init'}]


os.environ['STABILITY_HOST'] = 'grpc.stability.ai:443'
def gen_img(key, prompt):
    # Set up our connection to the API.
    stability_api = client.StabilityInference(
        key = key,
        verbose=True, # Print debug messages.
        engine="stable-diffusion-xl-1024-v1-0", # Set the engine to use for generation.
        # Available engines: stable-diffusion-v1 stable-diffusion-v1-5 stable-diffusion-512-v2-0 stable-diffusion-768-v2-0
        # stable-diffusion-512-v2-1 stable-diffusion-768-v2-1 stable-inpainting-v1-0 stable-inpainting-512-v2-0
    )

    # Set up our initial generation parameters.
    answers = stability_api.generate(
        prompt=prompt,
        seed=False, # If a seed is provided, the resulting generated image will be deterministic.
                        # What this means is that as long as all generation parameters remain the same, you can always recall the same image simply by generating it again.
                        # Note: This isn't quite the case for Clip Guided generations, which we'll tackle in a future example notebook.
        steps=50, # Amount of inference steps performed on image generation. Defaults to 30. 
        cfg_scale=8.0, # Influences how strongly your generation is guided to match your prompt.
                    # Setting this value higher increases the strength in which it tries to match your prompt.
                    # Defaults to 7.0 if not specified.
        width=1024, # Generation width, defaults to 512 if not included.
        height=1024, # Generation height, defaults to 512 if not included.
        samples=1, # Number of images to generate, defaults to 1 if not included.
        sampler=generation.SAMPLER_K_DPMPP_2M # Choose which sampler we want to denoise our generation with.
                                                    # Defaults to k_dpmpp_2m if not specified. Clip Guidance only supports ancestral samplers.
                                                    # (Available Samplers: ddim, plms, k_euler, k_euler_ancestral, k_heun, k_dpm_2, k_dpm_2_ancestral, k_dpmpp_2s_ancestral, k_lms, k_dpmpp_2m, k_dpmpp_sde)
    )
    
    try:
        for resp in answers:
            for artifact in resp.artifacts:
                if artifact.finish_reason == generation.FILTER:
                    warnings.warn(
                        "Your request activated the API's safety filters and could not be processed."
                        "Please modify the prompt and try again.")
                if artifact.type == generation.ARTIFACT_IMAGE:
                    photo_bytes = io.BytesIO(artifact.binary)
                    photo_file = types.InputFile(photo_bytes)
    except Exception as e:
        raise e

    return photo_file
    
async def editInMarkdown(user, text):
    if text != '':
        try:
            try:
                await user.currentReplyMsg.edit_text(text, parse_mode='Markdown')
            except aiogram.exceptions.MessageNotModified:
                pass
        except Exception:
            try:
                await user.currentReplyMsg.edit_text(text)
            except aiogram.exceptions.MessageNotModified:
                pass

