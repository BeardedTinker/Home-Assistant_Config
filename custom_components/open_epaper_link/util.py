
def get_image_folder(hass):
    """Return the folder where images are stored."""
    return hass.config.path("www/open_epaper_link")

def get_image_path(hass, entity_id):
    """Return the path to the image for a specific tag."""
    return hass.config.path("www/open_epaper_link/open_epaper_link."+ str(entity_id).lower() + ".jpg")