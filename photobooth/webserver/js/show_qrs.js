var picture = getUrlParameter('picture');

execute_api_call_get_single_picture(picture);

function execute_api_call_get_single_picture(picture){
  url = "api/get_picture/" + picture;
  console.log(url);
  var jqxhr = $.getJSON( url, function(data) {
    number_of_new_pictures = data['number_of_pictures'];
    if(number_of_new_pictures > 0)
    {
      show_new_pictures_popup(number_of_new_pictures)
    }
    append_new_pictures(data.new_pictures, view);
    show_photoboot_status(data.photobooth_status);
    t= data['last_picture']['picture_timestamp'];
  })
  .done(function(data) {
    console.log("ready")
  })
  .fail(function() {
    console.log("error");
  });
}
