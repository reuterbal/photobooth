console.log("Hello, i'm your shared javascript file.");

// For keyboard interaction
$(document).keyup(function(e) {
  console.log(e.keyCode);
  if (e.keyCode === 27) window.location.href = "/";  // esc > Go to index
  if (e.keyCode === 13 || e.keyCode === 83) window.location.href = "/slideshow";     // enter > Start slideshow
  if (e.keyCode === 71) window.location.href = "/gallery"
});


// https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Date/toLocaleTimeString
function format_datetime(datetimestamp, format){
  if(datetimestamp.toUpperCase() == "NOW"){
    d = new Date()
  }else {
    d = new Date(datetimestamp);
  }
  if(format.toUpperCase() == "TIME"){
    d = d.toLocaleTimeString(time_locale, time_format);
    return d;
  }
  if(format.toUpperCase() == 'DATETIME'){
    d = d.toLocaleTimeString(time_locale, datetime_format);
    return d;
  }
}

function update_clock()
{
  now_time = format_datetime('now', 'time');
  $("#clock").html("It's now:<p class='big status'>" + now_time + "</p>");
  setTimeout(update_clock, 1000);
}

t = 'all'
window.setInterval(function(){
  execute_api_call_get_new_pictures(t, view);
}, do_api_call_every_x_seconds * 1000);

function execute_api_call_get_new_pictures(timestamp, view)
{
  url = "api/get_new_pictures/" + timestamp;
  console.log(url);
  var jqxhr = $.getJSON( url, function(data) {
    number_of_new_pictures = data['number_of_pictures'];
    if(number_of_new_pictures > 0)
    {
      show_new_pictures_popup(number_of_new_pictures)
    }
    append_new_pictures(data.new_pictures, view);
    show_photoboot_status(data.photobooth_status);
    last_image = data['last_picture']
    t= data['last_picture']['picture_timestamp'];
  })
  .done(function(data) {
    console.log("ready")
  })
  .fail(function() {
    console.log("error");
  });
}

function show_new_pictures_popup(number)
{
  if(number==1)
  pictures = "picture was"
  else {
    pictures = "pictures were"
  }
  $("#new_pictures_added").html("Hooray, " + number + " new " + pictures + " taken...<p>Go and grab yours now!</p>").fadeIn().delay(show_new_pictures_popup_for_x_seconds * 1000).fadeOut();
}

function prepare_window(name, remove_container){
  $("<link/>", {
    rel: "stylesheet",
    type: "text/css",
    href: "/css/" + name + ".css"
  }).appendTo("head");

  $("<script/>", {
    type: "text/javascript",
    src: "/js/" + name + ".js"
  }).appendTo("head");

  $("body").addClass(name);

  if(remove_container){
    $(".container").removeClass();
  }

}

function append_new_pictures(picture_information, view){
  $.each( picture_information, function( key, value ) {
    generate_picture(key, value, view, "#picture_list");
    lst_images.push(value);

  });
}

function add_picture_html_view_for(i, view){

}

current_row = 0;
current_picture_number = 0;
function generate_picture(i, data, view, object){
  the_list = $(object);
  current_picture_number ++;
  console.log(current_picture_number);
  current_html_row = "";
  picture_name = data['picture_name'];
  picture_timestamp = data['picture_timestamp'];
  picture_datetime = data['picture_datetime'];
  picture_download_link = 'f/download/picture/' + picture_name;
  picture_show_link = 'f/show/picture/' + picture_name;
  if(view.toUpperCase() == 'SLIDESHOW')
  {
    the_list.append("<div class='mySlides myFade'><div class='numbertext'>" + current_picture_number + "</div><img src='/f/show/picture/" + picture_name +"' style='width:100%'><div class='text'>" + picture_datetime + "</div></div>");
  }

  if(view.toUpperCase() == 'GALLERY')
  {
    if(current_picture_number % gallery_number_of_columns == 0)
    {
      current_row++;
      $("#picture_list").prepend($('<div id="row_'+current_row+'" class="row">'));
    }
    $("#row_"+current_row).prepend("<div id='picture_" + current_picture_number + "'' class='" + gallery_column_width + "'><div class='picture_number'>Picture " + current_picture_number + "</div><img src='/f/show/picture/" + picture_name +"' style='width:100%'><div class='datetime'>" + format_datetime(picture_datetime, 'datetime') + "</div></div>");
    var delete_link = generate_link('delete', picture_name, current_picture_number, 'fa-trash', 'red');
    var download_link = generate_link('download', picture_name, current_picture_number, 'fa-download');
    var mail_link = generate_link('mail', picture_name, current_picture_number, 'fa-envelope');
    var show_link = generate_link('show', picture_name, current_picture_number, 'fa-glasses');
    var show_qr = generate_link('show_qrs', picture_name, current_picture_number, 'fa-qrcode');
    var print_picture = generate_link('print', picture_name, current_picture_number, 'fa-print');
    var my_action_list = $('<ul/>');
    my_action_list.attr('class', 'action_links');
    my_action_list.append(show_link).append(mail_link).append(download_link).append(show_qr).append(print_picture).append(delete_link);
    $("#picture_" + current_picture_number).append(my_action_list);
  }
}

function generate_link(function_to_do, picture, id, icon, color)
{
  var li = $('<li/>');
  var link = $('<a/>');
  var span = $('<span/>');
  span.attr('class', "fas " + icon)
  span.attr('style', 'color: '+color)
  if(function_to_do.toUpperCase() == "SHOW_QRS")
  {
    link.attr('href', 'show_qrs?picture=' + picture);
  }
  else link.attr('href', 'f/' + function_to_do + '/picture/' + picture_name);
  link.attr('id', function_to_do + "_" + id)
  link.append(span);

  return li.append(link);
}

function show_photoboot_status(status)
{
  $("#photobooth_status").html("Photobooth status: <p class='big status " + status + "'>" + status + "</p>")
}


var getUrlParameter = function getUrlParameter(sParam) {
    var sPageURL = window.location.search.substring(1),
        sURLVariables = sPageURL.split('&'),
        sParameterName,
        i;

    for (i = 0; i < sURLVariables.length; i++) {
        sParameterName = sURLVariables[i].split('=');

        if (sParameterName[0] === sParam) {
            return sParameterName[1] === undefined ? true : decodeURIComponent(sParameterName[1]);
        }
    }
};
