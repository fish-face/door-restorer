<?xml version="1.0" encoding="UTF-8"?>
<tileset name="Objects" tilewidth="24" tileheight="24">
 <image source="../graphics/tiles-object.png" width="240" height="24"/>
 <tile id="0">
  <properties>
   <property name="name" value="player"/>
  </properties>
 </tile>
 <tile id="1">
  <properties>
   <property name="name" value="door"/>
  </properties>
 </tile>
 <tile id="2">
  <properties>
   <property name="name" value="door"/>
   <property name="state" value="open"/>
  </properties>
 </tile>
 <tile id="3">
  <properties>
   <property name="name" value="player"/>
   <property name="state" value="holding-door"/>
  </properties>
 </tile>
 <tile id="4">
  <properties>
   <property name="name" value="player"/>
   <property name="state" value="awaiting-input"/>
  </properties>
 </tile>
 <tile id="5">
  <properties>
   <property name="name" value="player"/>
   <property name="state" value="awaiting-throw"/>
  </properties>
 </tile>
</tileset>
