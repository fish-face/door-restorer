<?xml version="1.0" encoding="UTF-8"?>
<tileset name="Terrain" tilewidth="24" tileheight="24">
 <image source="../graphics/tiles-terrain.png" width="240" height="24"/>
 <tile id="0">
  <properties>
   <property name="name" value="wall"/>
  </properties>
 </tile>
 <tile id="1">
  <properties>
   <property name="name" value="floor"/>
  </properties>
 </tile>
 <tile id="2">
  <properties>
   <property name="name" value="pit"/>
  </properties>
 </tile>
 <tile id="3">
  <properties>
   <property name="name" value="pickup"/>
  </properties>
 </tile>
 <tile id="4">
  <properties>
   <property name="name" value="goal"/>
  </properties>
 </tile>
 <tile id="5">
  <properties>
   <property name="name" value="pickup"/>
   <property name="state" value="wall-up"/>
  </properties>
 </tile>
 <tile id="6">
  <properties>
   <property name="name" value="pickup"/>
   <property name="state" value="wall-right"/>
  </properties>
 </tile>
 <tile id="7">
  <properties>
   <property name="name" value="pickup"/>
   <property name="state" value="wall-down"/>
  </properties>
 </tile>
 <tile id="8">
  <properties>
   <property name="name" value="pickup"/>
   <property name="state" value="wall-left"/>
  </properties>
 </tile>
 <tile id="9">
  <properties>
   <property name="name" value="pickup"/>
   <property name="state" value="null"/>
  </properties>
 </tile>
</tileset>
