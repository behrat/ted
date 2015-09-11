<?php
$svn_version = trim(shell_exec('svnversion'));

mysql_connect('localhost', 'ted', 'qPueHNCFFv2CVSS6') or die(mysql_error());
mysql_select_db('ted') or die(mysql_error());

if(isset($_GET['port'])) {
  $socket_io_port = $_GET['port'];
} else {
  $socket_io_port = 35000;
}

$inputs = array();
$result = mysql_query("SELECT in_id AS id, in_name AS name, in_local_out AS local_out FROM input") or die(mysql_error());
while($row = mysql_fetch_assoc($result)) {
  $inputs[] = $row;
}


$outpus = array();
$result = mysql_query("SELECT out_id AS id, out_name AS name FROM output") or die(mysql_error());
while($row = mysql_fetch_assoc($result)) {
  $outputs[] = $row;
}
?>
<!doctype html>
<html>
<head>
<title>&#9834; TED</title>
<script>
var socket_io_uri = ":<?=$socket_io_port?>";
var svn_version = "<?=$svn_version?>";
</script>
<script src="//<?=$_SERVER['HTTP_HOST']?>:<?=$socket_io_port?>/socket.io/socket.io.js"></script>
<script src="/lib/jquery/js/jquery.min.js"></script>
<script src="/lib/jquery/js/jquery-ui.min.js"></script>
<script src="index.js"></script>
<link rel="Stylesheet" type="test/css" href="/lib/jquery/css/vader/jquery.ui.theme.css" />
<link rel="Stylesheet" type="text/css" href="index.css" />
<link rel="shortcut icon" type="image/x-icon" href="/favicon.ico" />
</head>
<body>
<h3>&#9835; Tribonacci Entertainment Distribution &#9835;</h3>
<table border=1>
<tbody>
  <tr>
    <th colspan=6>Inputs</th>
    <th rowspan=2>Outputs</th>
  </tr>

  <tr>
<?php foreach($inputs as $in) { ?>
    <th class="input" style="margin:0px; padding:0px;">
      <div style="position:relative; margin:0px; padding:0px; height:100%;">
        <div style="position:absolute; margin:0px; padding:0px; height:100%;" class="level" id="input-level-<?=$in['id']?>"></div>
        <?=$in['name']?>
      </div>
    </th>
<?php } ?>
  </tr>

  <tr>
<?php foreach($inputs as $in) { ?>
    <td>
      <select class='macro' element="input" in=<?=$in['id']?> out=<?=$in['local_out']?>>
        <option value='blank'>&darr;</option>
        <option value='all'>All</option>
        <option value='solo'>Solo</option>
<?php if(!is_null($in['local_out'])) { ?>
        <option value='local'>Local</option>
<?php } ?>
        <option value='off'>Off</option>
      </select>
    </td>
<?php } ?>
<?php /*    <td></td> */ ?>
    <td>
      <select class='macro' element="general">
        <option value='blank'></option>
        <option value='all-on'>All On</option>
        <option value='mute-all'>Mute All</option>
      </select>
    </td>
  </tr>

<?php foreach($outputs as $out) { ?>
  <tr>
<?php foreach($inputs as $in) { ?>
    <td id="matrix-mute-<?=$in['id']?>-<?=$out['id']?>" class="mute" element="matrix" in=<?=$in['id']?> out=<?=$out['id']?>></td>
<?php } ?>
<?php /*    <td>
      <select class="macro" element="output" out=<?=$out['id']?>>
        <option value='blank'>&rarr;</option>
<?php foreach($inputs as $in) { ?>
        <option value='<?=$in['id']?>'><?=$in['name']?></option>
<?php } ?>
      </select>
    </td> */ ?>
    <td id="output-mute-<?=$out['id']?>" class="mute" element="output" out=<?=$out['id']?>><?=$out['name']?></td>
  </tr>
<?php } ?>
</tbody>
</table>
</body>
</html>
