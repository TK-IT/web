permlinkBase = "";
galleryContainer = ".tkgal_container";

// skjuler alt undtagen det ønskede element med attributen permlink="permlink"
function changeCurrent(permlink) {
  loadContent(permlink);
  $elements=$(galleryContainer+" > *")
  $elements.removeClass("current"); // skjul nuværende
  numberOfElements = $elements.length;

  $current =$("[permlink="+permlink+"]");
  $current.addClass("current"); // vis ønskede

  window.history.replaceState(null,null, permlink); // tilpas viste url i browseren (skal tilpasses django url til samme indhold)

  prevIndex = ($current.index() - 1)%numberOfElements;
  nextIndex = ($current.index() + 1)%numberOfElements;
  prevPermlink=$(galleryContainer+" > *").eq(prevIndex).attr("permlink");
  nextPermlink=$(galleryContainer+" > *").eq(nextIndex).attr("permlink");
  
  $(".tkgal_link.prev").attr("link", prevPermlink);
  $(".tkgal_link.next").attr("link", nextPermlink);
  
  url_base = $(".tkgal_url_base").attr("href");
  $(".tkgal_link.prev").attr("href", url_base + "/" + prevPermlink);
  $(".tkgal_link.next").attr("href", url_base + "/" + nextPermlink);
  
  
  loadContent(prevPermlink);
  loadContent(nextPermlink);
}

// load indhold, ved at fjerne dummy-attributer
function loadContent(permlink) {
	$("[permlink="+permlink+"] [data-src]").each(function( index ) {
		$(this).replaceWith($(this)[0].outerHTML.replace("data-src=","src="));
	});
	$("[permlink="+permlink+"] [data-srcset]").each(function( index ) {
		$(this).replaceWith($(this)[0].outerHTML.replace("data-srcset=","srcset="));
	});
	
	// for media that do not have a parent
	$("[permlink="+permlink+"][data-src]").each(function( index ) {
		$(this).replaceWith($(this)[0].outerHTML.replace("data-src=","src="));
	});
}


// simulate link press when arrow keys are pressed
document.onkeyup = KeyCheck;       
function KeyCheck(e) {
  var KeyID = (window.event) ? event.keyCode : e.keyCode;
  switch(KeyID) {
    case 37:
        $(".tkgal_link.prev")[0].click();
    break;
    case 39:
         $(".tkgal_link.next")[0].click();
    break;
   }
}

// 
$(document).ready(function() {
	
	$(".tkgal_link").click(function(e) {
	  e.preventDefault();
	  changeCurrent( $(this).attr("link") );
	});
  
  $(".tkgal_container > *").swipe( {
    swipe:function(event, direction, distance, duration, fingerCount, fingerData) {
    switch(direction) {
      case "left":
        $(".tkgal_link.next")[0].click();
        break;
      case "right":
        $(".tkgal_link.prev")[0].click();
        break;
      default:
}
    }
  });

});