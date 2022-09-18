<html>
<head>
<title>SUCCESSFUL REGISTRATION</title>
<script type="text/javascript">
function back(){
	window.location.href="RegistrationForm.html";
}
</script>
<link rel="stylesheet" href="stylesuccess.css">
</head>
<body>
<div>Thanks for registering!</div><br><br>
<?php
$name=$_POST['name'];
$regno=$_POST['regno'];
$email=$_POST['email'];
$pwd=$_POST['pwd'];
$branch=$_POST['branch'];
$gen=$_POST['gen'];
$exp=$_POST['exp'];
echo "<table>";
echo "<tr>";
echo "<th>NAME</th>";
echo "<th>REGISTRATION NUMBER</th>";
echo "<th>EMAIL ID</th>";
echo "<th>PASSWORD</th>";
echo "<th>DEPARTMENT</th>";
echo "<th>GENDER</th>";
echo "<th>EXPECTATION</th>";
echo "</tr>";
echo "<td>$name</td>";
echo "<td>$regno</td>";
echo "<td>$email</td>";
echo "<td>$pwd</td>";
echo "<td>$branch</td>";
echo "<td>$gen</td>";
echo "<td>$exp</td>";
echo "</tr>";
echo "</table>";
?>
<br><br>
<button onclick="back()">BACK</button>
</body>
</html>