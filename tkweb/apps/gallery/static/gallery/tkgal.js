$(document).ready(function() {
    // Get array of all slugs
    var slugs = $("#tkgal-container > *").map(function() {
        return $(this).attr("permlink");
    }).get();

    // Call changeCurrent on click on the controls
    $(".tkgal-control").click(function(e) {
        e.preventDefault();
        pauseMedia();
        changeCurrent($(this).attr("href"));
    });

    function changeCurrent(newimage) {
        // Calculate prev and next images
        var l = slugs.length;
        var i = slugs.indexOf(newimage);
        var prev = slugs[(((i-1)%l)+l)%l]; // mod is broken for negative numbers
        var next = slugs[(i+1)%l];

        // Update visibility of current picture
        $("#tkgal-container > div").removeClass("current");
        $("[permlink='"+newimage+"']").addClass("current");

        // Rename the prev and next img's data-srcset to srcset
        function changeSrcset(image) {
            var i = $("[permlink='"+image+"'] > img");
            i.attr('srcset', i.attr('data-srcset'));
            i.removeAttr('data-srcset');
        }
        changeSrcset(prev);
        changeSrcset(next);

        // Update 'i of l images' index
        $("#tkgal-index").html(i+1);

        // Update prev/next links
        $("#tkgal-prev").attr("href", prev);
        $("#tkgal-next").attr("href", next);

        // Rewrite history
        window.history.replaceState(null, null, newimage);
    }

    function pauseMedia() {
        if ($(".current > video").length) {
            $(".current > video").get(0).pause();
        }
        if ($(".current > audio").lenght) {
            $(".current > audio").get(0).pause();
        }
    }

    // Call swipehandler on swipe
    // This requires jquery touchswipe
	$("body").swipe( { // register swipe anywhere in body
        swipeLeft:swipehandler,
        swipeRight:swipehandler,
        allowPageScroll:"auto"
		
    });

    function swipehandler(event, direction) {
        switch(direction) {
        case "left":
            $("#tkgal-next")[0].click();
            break;
        case "right":
            $("#tkgal-prev")[0].click();
            break;
        default:
        }
    }
});

// simulate link press when arrow keys are pressed
$(document).keydown(function(e) {
    switch(e.which) {
    case 37: // left
        $("#tkgal-prev")[0].click();
        break;
    case 39: // right
        $("#tkgal-next")[0].click();
        break;
    }
});
