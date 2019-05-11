console.log("Hello, i'm your last_picture.js file");
window.setInterval(function(){
  console.log("kiekeboe");
  set_last_picture_info("#last_image", "#last_picture", last_image);
}, do_api_call_every_x_seconds * 1000);

function set_last_picture_info(id, picture_container, data){
  // my_img = $(picture_container);
  // my_img.attr("style","f/show/picture/"+data.picture_name);
  $('body').css('background-image', 'url(/f/show/picture/' + data.picture_name + ')');
  $('#picture_timestamp p').text(format_datetime(data.picture_datetime, 'DATETIME'));
  $('#mail_qr').attr('src', '/f/mail_qr/picture/' + data.picture_name);
  $('#download_qr').attr('src','/f/download_qr/picture/' + data.picture_name);
}
