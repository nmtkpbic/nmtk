from django.db.models.signals import post_save
from django.dispatch import receiver
from NMTK_server import models
from NMTK_server import tasks
import logging
import requests
from django.core.exceptions import ObjectDoesNotExist
logger=logging.getLogger(__name__)

@receiver(post_save, sender=models.Job)
def sendJobToTool(sender, instance, **kwargs):
    '''
    Rather than have the view code have to submit the job, we'll just 
    monitor the job table.  Whenever a job gets configured, the
    state change from unconfigured to configured will trigger 
    sending the job to the client - so we have a single entry point
    for sending jobs to the client.
    
    In the interest of speed, the job execution work (which might take 
    some time to submit) is passed off as a celery task, so the client gets
    it's response(s) back immediately.
    '''
    if instance._old_status == 'U' and instance.status == 'A':
        logger.debug('Detected a state change from Unconfigured to Active.')
        logger.debug('Sending job to tool for processing.')
        # Submit the task to the client, passing in the job identifier.
        tasks.submitJob.delay(instance)

@receiver(post_save, sender=models.ToolServer)
def updateTools(sender, instance, **kwargs):
    '''
    Whenever a toolserver record is saved (and it's not a new record) we will
    go out and discover its tools.
    '''
    logger.debug('Detected a save of the ToolServer model, adding/updating tools.')
    url="%s/index" % (instance.server_url) # index returns a json list of tools.
    tool_list=requests.get(url).json()
    logger.debug('Retrieved tool list of: %s', tool_list)
    for tool in tool_list:
        try:
            t=models.Tool.objects.get(tool_server=instance,
                                      tool_path=tool)
        except ObjectDoesNotExist:
            t=models.Tool(tool_server=instance,
                          name=tool)
        t.active=True
        t.tool_path=tool
        t.name=tool
        t.save()
    
    # Locate all the tools that aren't there anymore and disable them.
    for row in models.Tool.objects.exclude(tool_path__in=tool_list).filter(active=True):
        logger.debug('Disabling tool %s', row.name)
        row.active=False
        row.save()

@receiver(post_save, sender=models.Tool)
def updateToolConfig(sender, instance, **kwargs):
    '''
    Whenever a tool record is added or saved, we go out to the tool
    and retrieve/update it's configuration within the tool server.
    '''
    if instance.active:
        logger.debug('Detected a save of the Tool model, updating configs.')
        json_config=requests.get(instance.config_url)
        try:
            config=instance.toolconfig
        except:
            config=models.ToolConfig(tool=instance)
        config_data=json_config.json()
        config.json_config=config_data
        config.save()
        # Note: We use update here instead of save, since we want to ensure that
        # we don't call the post_save handler, which would result in
        # a recursion loop.
        models.Tool.objects.filter(pk=config.tool.pk).update(name=config_data['info']['name'])
                   