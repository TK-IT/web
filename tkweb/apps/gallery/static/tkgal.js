$(document).ready(function() {
    // Get array of all slugs
    var slugs = $("#tkgal-container > *").map(function() {
        return $(this).attr("permlink");
    }).get();

    // Call changeCurrent on click on the controls
    $(".tkgal-control").click(function(e) {
        e.preventDefault();
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

        // Update 'i of l images' index
        $("#tkgal-index").html(i+1);

        // Update prev/next links
        $("#tkgal-prev").attr("href", prev);
        $("#tkgal-next").attr("href", next);

        // Rewrite history
        window.history.replaceState(null, null, newimage);
    }

    // Call swipehandler on swipe
    // This requires jquery touchswipe
    $(".tkgal-container > *").swipe( {
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
