$(document).ready(function() {
    var slugs = $("#tkgal-container > *").map(function() {
        return $(this).attr("permlink");
    }).get();

    $(".tkgal-control").click(function(e) {
        e.preventDefault();
        changeCurrent( $(this).attr("href"));
    });

    function changeCurrent(permlink) {
        $("#tkgal-container > div").removeClass("current");
        $("[permlink='"+permlink+"']").addClass("current");
        window.history.replaceState(null, null, permlink);

        var l = slugs.length;
        var i = slugs.indexOf(permlink);
        var pi = (((i-1)%l)+l)%l; // js modulo is broken for negative numbers.
        var ni = (i+1)%l;
        $("#tkgal-prev").attr("href", slugs[pi]);
        $("#tkgal-next").attr("href", slugs[ni]);
    }

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
