$(function() {


function createModalDialog(title, html) {
return $("<div/>").html(html)
    .dialog({
      title: title,
      resizable: false,
      draggable: false,
      autoOpen: false,
      modal: true,
      dialogClass: 'no-close',
      buttons: {"Refesh": function() { location.reload(true); } },
    });
}

var socket_options = {
  'connect timeout':1000,
  'reconnect': false,
// 'reconnection delay': 500,
//  'max reconnection attempts': 2,
}

try {
  var socket = io.connect(socket_io_uri, socket_options);
} catch(err) {
  createModalDialog("Error",
    "Could not connect to the TED control server.")
  .dialog('open');
  return;
}

var load_date = new Date();

var dialogs = {};
dialogs.disconnected = createModalDialog("Disconnected", 
  "<p>Please refresh to attempt reconnect.</p>"
);//.dialog("option", "buttons", [ {text: "Ok", click: function() { location.reload(true); } } ]);



console.log(socket);
socket.on('connect', function() {
  console.log("connected");
});

socket.on('connecting', function(type) {
  console.log('connecting: ' + type);
});

socket.on('connect_failed', function() {
  console.log('connect_failed');
});

socket.on('disconnect', function() {
  console.log('disconnect');
  dialogs.disconnected.dialog('open');
  $("td").removeClass('muted').removeClass('unmuted');
});

socket.on('reconnecting', function(delay, attempts) {
  console.log('roconnecting: ' + delay + " attempts: " + attempts);
});

socket.on('reconnect_failed', function() {
  console.log('reconnect_failed');
});

//$("#dialog-disconnected").dialog('open');

socket.on('message', function(message) {
  var data = JSON.parse(message);
  //console.log(data)

  for(var i in data) {
    var stat = data[i];

    if(stat.e == 'i') {
      var cell = $("#input-level-"+stat.i);
      if(stat.level >= 100) {
        stat.level = 100

        // clear any existing timer to remove the peak and start a new one
        clearTimeout(cell.data("peak_timer"));
        cell.addClass("peaked");
        cell.data("peak_timer", setTimeout(function() {cell.removeClass("peaked");}, 250));
      }

      // stop any current playing or queued animation
      cell.stop(true)

      // set the new level
      cell.css("width", stat.level + "%");

      // animiate width back towards 0
      cell.animate({width:"0%"}, {
        duration: (1000 * stat.level)/100,
      });

      continue;
    }

    if(stat.e == 'version') {
      if(stat.version != svn_version) {
         // force refresh from server only if we haven't recently
         if(new Date - load_date > 20 * 1000) {
           location.reload(true);
         }
      }
    }

    if(stat.e == 'matrix') {
      var cell = $("#matrix-mute-"+stat.i+"-"+stat.o);
    } else if (stat.e == 'output') {
      var cell = $("#output-mute-"+stat.o);
    }

    if('muted' in stat) {
      if(stat.muted == false) {
        cell.removeClass('muted');
        cell.addClass('unmuted');
      } else {
        cell.removeClass('unmuted');
        cell.addClass('muted');
      }
    }
  }

});
/*
socket.on('disconnect', function() {
 $("#disconnect-dialog").dialog('open');

});
*/

$(".mute").on('click', function(event) {
  cell = $(event.target);

  command = {
    command: 'element',
    element: cell.attr('element'),
    attr: 'muted',
    i: parseInt(cell.attr('in')),
    o: parseInt(cell.attr('out')),
    meta: event.metaKey,
  };

  if(cell.hasClass('muted')) {
    cell.removeClass('muted');
    command.value = false;
  } else if (cell.hasClass('unmuted')) {
    cell.removeClass('unmuted');
    command.value = true;
  } else {
    // there must be one pending
    return;
  }

  socket.send(JSON.stringify(command));
});

$(".macro").change(function(event) {
  selector = $(event.target);
  if(selector.attr('value') == 'blank') return;

  command = {
    command: 'macro',
    i: parseInt(selector.attr('in')),
    o: parseInt(selector.attr('out')),
    element: selector.attr('element'),
    macro: selector.attr('value'),
  }

  selector.attr('value', 'blank');

  socket.send(JSON.stringify(command));
});

});
