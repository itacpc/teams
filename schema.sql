create table universities(
    id text primary key,
    name text not null,
    domain text not null
);

create table teams(
    id serial primary key,
    name text not null,
    university text not null,
    secret text not null unique,
    creation_date timestamp not null default current_timestamp,
    credentials json,
    foreign key(university) references universities(id)
);

create table students(
    id serial primary key,
    first_name text not null,
    last_name text not null,
    email text not null unique,
    password text,
    university text not null,
    team integer,
    confirmed boolean default FALSE,
    subscribed boolean default TRUE,
    codeforces_handle text,
    kattis_handle text,
    olinfo_handle text,
    github_handle text,
    secret text not null unique,
    secret_valid_until timestamp,
    creation_date timestamp not null default current_timestamp,
    foreign key(university) references universities(id),
    foreign key(team) references teams(id),
    check ((confirmed is true) = (password is not null))
);

create table teamjoinlog(
    id serial primary key,
    student integer not null,
    team integer not null,
    joining boolean not null,
    creation_date timestamp not null default current_timestamp
);

insert into universities(id, name, domain) values
    -- ('other', 'No university / Foreign university', '*'),
    -- ('iuss', 'Istituto Universitario di Studi Superiori', 'iusspavia.it'),
    ('luiss', 'Libera Università Internazionale degli Studi Sociali "Guido Carli"', 'luiss.it,luiss.edu'),
    ('poliba', 'Politecnico di Bari', 'poliba.it'),
    ('polimi', 'Politecnico di Milano', 'polimi.it'),
    ('polito', 'Politecnico di Torino', 'polito.it'),
--     ('imtlucca', 'Scuola IMT Alti Studi Lucca', 'imtlucca.it'),
    ('sns', 'Scuola Normale Superiore', 'sns.it'),
    ('santanna', 'Scuola superiore di studi universitari e di perfezionamento Sant''Anna', 'santannapisa.it'),
    ('unive', 'Università Ca'' Foscari di Venezia', 'unive.it'),
    ('unibas', 'Università degli Studi della Basilicata', 'unibas.it'),
    ('unical', 'Università degli Studi della Calabria', 'unical.it'),
    ('unicampania', 'Università degli Studi della Campania "Luigi Vanvitelli"', 'unicampania.it'),
    ('univaq', 'Università degli Studi dell''Aquila', 'univaq.it'),
    ('unitus', 'Università degli Studi della Tuscia', 'unitus.it'),
    ('uninsubria', 'Università degli Studi dell''Insubria', 'uninsubria.it'),
    ('unimol', 'Università degli Studi del Molise', 'unimol.it'),
    ('uniupo', 'Università degli Studi del Piemonte Orientale "Amedeo Avogadro"', 'uniupo.it'),
    ('unisalento', 'Università degli Studi del Salento', 'unisalento.it'),
    ('unisannio', 'Università degli Studi del Sannio', 'unisannio.it'),
    ('uniba', 'Università degli Studi di Bari Aldo Moro', 'uniba.it'),
    ('unibg', 'Università degli Studi di Bergamo', 'unibg.it'),
    ('unibo', 'Università degli Studi di Bologna', 'unibo.it'),
    ('unibs', 'Università degli Studi di Brescia', 'unibs.it'),
    ('unibz', 'Libera Università di Bolzano', 'unibz.it'),
    ('unica', 'Università degli Studi di Cagliari', 'unica.it'),
    ('unicam', 'Università degli Studi di Camerino', 'unicam.it'),
    ('unicas', 'Università degli Studi di Cassino e del Lazio Meridionale', 'unicas.it'),
    ('unict', 'Università degli Studi di Catania', 'unict.it'),
--     ('unicz', 'Università degli Studi di Catanzaro "Magna Græcia"', 'unicz.it'),
    ('unife', 'Università degli Studi di Ferrara', 'unife.it'),
    ('unifi', 'Università degli Studi di Firenze', 'unifi.it'),
--     ('unifg', 'Università degli Studi di Foggia', 'unifg.it'),
    ('unige', 'Università degli Studi di Genova', 'unige.it'),
--     ('unimc', 'Università degli Studi di Macerata', 'unimc.it'),
    ('unime', 'Università degli Studi di Messina', 'unime.it'),
    ('unimi', 'Università degli Studi di Milano', 'unimi.it'),
    ('unimib', 'Università degli Studi di Milano-Bicocca', 'unimib.it'),
    ('unimore', 'Università degli Studi di Modena e Reggio Emilia', 'unimore.it'),
    ('unina', 'Università degli Studi di Napoli "Federico II"', 'unina.it'),
--     ('unior', 'Università degli Studi di Napoli "L''Orientale"', 'unior.it'),
    ('uniparthenope', 'Università degli Studi di Napoli "Parthenope"', 'uniparthenope.it'),
    ('unipd', 'Università degli Studi di Padova', 'unipd.it'),
    ('unipa', 'Università degli Studi di Palermo', 'unipa.it'),
    ('unipr', 'Università degli Studi di Parma', 'unipr.it'),
    ('unipv', 'Università degli Studi di Pavia', 'unipv.it'),
    ('unipg', 'Università degli Studi di Perugia', 'unipg.it'),
    ('unipi', 'Università degli Studi di Pisa', 'unipi.it'),
    ('unirc', 'Università degli Studi di Reggio Calabria "Mediterranea"', 'unirc.it'),
--     ('uniroma4', 'Università degli Studi di Roma "Foro Italico"', 'uniroma4.it'),
    ('uniroma1', 'Università degli Studi di Roma "La Sapienza"', 'uniroma1.it'),
    ('uniroma2', 'Università degli Studi di Roma Tor Vergata', 'uniroma2.it'),
    ('unisa', 'Università degli Studi di Salerno', 'unisa.it'),
    ('uniss', 'Università degli Studi di Sassari', 'uniss.it'),
    ('unisi', 'Università degli Studi di Siena', 'unisi.it'),
    ('unite', 'Università degli Studi di Teramo', 'unite.it'),
    ('unito', 'Università degli Studi di Torino', 'unito.it'),
    ('unitn', 'Università degli Studi di Trento', 'unitn.it'),
    ('units', 'Università degli Studi di Trieste', 'units.it'),
    ('uniud', 'Università degli Studi di Udine', 'uniud.it'),
    ('uniurb', 'Università degli Studi di Urbino "Carlo Bo"', 'uniurb.it'),
    ('univr', 'Università degli Studi di Verona', 'univr.it'),
    ('unich', 'Università degli Studi "Gabriele d''Annunzio"', 'unich.it'),
    ('uniroma3', 'Università degli Studi Roma Tre', 'uniroma3.it'),
    -- ('iuav', 'Università Iuav di Venezia', 'iuav.it'),
    -- ('unistrapg', 'Università per Stranieri di Perugia', 'unistrapg.it'),
    -- ('unistrasi', 'Università per Stranieri di Siena', 'unistrasi.it'),
    ('univpm', 'Università Politecnica delle Marche', 'univpm.it');
