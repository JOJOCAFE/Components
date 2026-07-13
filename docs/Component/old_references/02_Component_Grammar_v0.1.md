# Component Grammar v0.1

## Keywords

use component board operation schema device group module connect net bus
probe watch inject is as

## Comments

// single line

/\* multi line \*/

## Top Level

component:component Name { }

component:board Name { }

component:operation Name { }

component:schema Name { }

## Device

device Counter is 74HC161;

device LED\[4\] is LED;

## References

Counter.CLK Counter./CS Counter.@2

LED\[0\] LED\[0..3\]

Counter.Q\[0..3\]

## Alias

Counter\[Q0,Q1,Q2,Q3\] as Counter.Q\[0..3\];

## Connection

connect A -\> B;

Mappings: 1-\>1 1-\>N N-\>1 N-\>N

Unequal many-to-many =\> error.

## Inject

inject noise into Clock.OUT;

inject boot.bin into ROM;

## Probe

probe Counter.Q\[0..3\];

watch Counter.Q\[0..3\];

## Tick

connect tick(120) -\> Reset.IN;

## Rule

Write for humans first.
