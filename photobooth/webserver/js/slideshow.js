console.log("I'm your slideshow script!");

showSlides();
update_clock();

function generate_full_screen_info(){
  picture_name = lst_images[slideIndex-1]['picture_name'];
  picture_datetime = lst_images[slideIndex-1]['picture_datetime'];
  picture_number = slideIndex;

  $("#fullscreen_info").removeClass("hidden");
  $("#picture_name").text(picture_name);
  $("#picture_datetime").text(format_datetime(picture_datetime, 'datetime'));
  $("#picture_number").text("Picture " + picture_number + " of " + lst_images.length);
}

var slideIndex = 0;
function showSlides() {
  var i;
  var slides = document.getElementsByClassName("mySlides");
  // console.log(slides);
  // console.log(slides.length);
  if(slides.length > 0){
    for (i = 0; i < slides.length; i++) {
      slides[i].style.display = "none";
    }
    slideIndex++;
    if (slideIndex > slides.length) {slideIndex = 1}
    if(show_in_fullscreen)
    {
      $('body').css('background-image', 'url(/f/show/picture/' + lst_images[slideIndex-1]['picture_name'] + ')');
      generate_full_screen_info();
    }
    else {
      slides[slideIndex-1].style.display = "block";
    }
  }
  setTimeout(showSlides, change_slides_every_x_secondes * 1000);
}
