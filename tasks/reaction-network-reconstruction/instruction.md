We ran a small aqueous carbonyl system in a steady flow reactor and we have the analytics
but not the mechanism. The raw evidence is in /app/data: the species we can see with their
drawn structures, a list of candidate reactions somebody on the team wrote down as
plausible, the reactor conditions, the steady-state concentrations, the measured net
production rates, three tracer runs, thermodynamic estimates, and three isomers any one of
which could be the C5H7O4- signal we keep seeing but have never assigned. Your job is to
work out which of those candidates are actually running, what each one does at the atom
level, how fast it runs and which way, and to say why each of the rest is out. Write the
result to /app/network.json.

Some ground rules that are particular to how we work, because they are not all the
convention elsewhere.

The drawn structures are authoritative. Each species record carries both a typed formula
string and an explicit atom-and-bond structure, and somebody has fat-fingered the strings.
Where the two disagree, the structure is right. List every species where they disagree in
formula_conflicts.

Candidate reactions are given as the species on each side and nothing more. You determine
the coefficients: the smallest positive integers that balance every element and the total
charge. Hydrogen and charge both count. If no such set of coefficients exists the candidate
is unbalanceable. If the two sides admit more than one independent balance, the candidate is
ambiguous_balance, and it is out even though a balance exists.

An atom map pairs every non-hydrogen atom on one side of a reaction with an atom of the
same element on the other. Many pairings balance, so we fix one: take the pairings that keep
the largest number of bonds, where a bond counts as kept only if the two mapped partners are
bonded on the other side at the same bond order. If several pairings tie, write each pairing
as the two strings "SPECIES#INSTANCE:ATOM" and take the one whose sorted list of pairs is
smallest lexicographically. Instances are numbered from 1 and only matter when a coefficient
is above 1.

The free energies in the candidate file are estimates quoted at the reference temperature
named in that same file, and the reactor is not at that temperature. Report delta_r_g as the
reaction free energy under the actual reactor conditions, in kJ/mol, with the reaction
enthalpy and entropy treated as constant over that interval and the solvent taken at unit
activity. Our concentration data resolve that number to about half a kJ/mol, so treat a
reaction whose delta_r_g comes out within 0.5 of zero, in either direction, as equilibrated
and set equilibrium true for it. An equilibrated reaction is part of the network whether or
not it carries any net flow, and equilibrated is not the same thing as standing still: two
of ours are equilibrated and still carry real flux.

Reaction classes gate on the reactor. Each candidate declares a class, each class declares
what it needs, and the conditions file says what the reactor has. A candidate whose class
needs something the reactor does not have is condition_gated.

The tracer runs veto connectivity. For each run you get the enrichment we put into the feed
and the enriched positions we then measured. Take a candidate's own atom map and push the
measured enrichment across it, in whichever direction its free energy permits, both ways if
it is equilibrated. If that puts enrichment on a position of a species the same run reports
on and reports clean, the candidate is isotope_inconsistent. Only species that run actually
reports on constrain anything.

What survives all of that has to account for the measured net rates exactly, all of them at
once, with one flux per reaction. Flux is signed against the direction the candidate file
writes the reaction in, so a negative flux means it runs the other way. A survivor that the
rate data force to zero flux, and that is not equilibrated, is no_net_flux. Everything still
standing is the network. Set direction to forward for positive flux, reverse for negative,
balanced for zero.

Rules go in that order and you report the first one that removes a candidate: balance, then
the isomer identity, then the class gate, then the tracers, then the flux. Several candidates
would be caught by more than one, and we want to know which one caught it first. The reason
strings are exactly these, no others: unbalanceable, ambiguous_balance, intermediate_mismatch,
condition_gated, isotope_inconsistent, no_net_flux. A candidate that names an isomer you did
not identify is intermediate_mismatch.

Every candidate id appears exactly once across the network and the exclusions, never in both
and never in neither.

Call intermediates the species the network both makes and consumes, judged on the direction
each reaction actually runs and ignoring reactions that carry no net flow, minus anything the
feed supplies. The feed list is in the conditions file.

For label_predictions, do not just echo the measurements back. Start from the feed enrichment
of each run and propagate it through the network you reconstructed until nothing more
changes, following the direction each reaction actually runs, and both directions for
equilibrated ones. Report the enriched positions this predicts for every species that ends up
enriched, including ones we never measured.

The output is a single JSON object at /app/network.json with these keys. intermediate_id is
the id of the isomer you assigned to the C5H7O4- channel. formula_conflicts is a sorted list
of species ids. reactions is a list, one entry per reaction in the network, each with id,
coefficients as an object with reactants and products mapping species id to integer
coefficient, delta_r_g rounded to two decimals, equilibrium as a boolean, direction, net_flux
in the same units as the rate data rounded to three decimals, and atom_map as a list of
two-element lists of those atom reference strings. excluded is a list of objects with id and
reason. intermediates is a sorted list of species ids. label_predictions maps each run id to
an object mapping species id to its sorted list of enriched atom ids, leaving out species
with no enrichment.

There is a script at /app/validate_output.py that checks the shape of the file and the
internal consistency of what you wrote, and says nothing about whether the chemistry is
right. Run it on your output before you finish.

You have 10800 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
