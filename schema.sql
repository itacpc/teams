create table universities(
    id text primary key,
    name text not null,
    domain text not null,
    kattis_subdivision text
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

insert into universities(id, name, domain, kattis_subdivision) values
    -- ('imtlucca', 'Scuola IMT Alti Studi Lucca', 'imtlucca.it', null),
    -- ('iuav', 'Università Iuav di Venezia', 'iuav.it', null),
    -- ('iuss', 'Istituto Universitario di Studi Superiori', 'iusspavia.it', null),
    -- ('other', 'No university / Foreign university', '*', null),
    -- ('unicz', 'Università degli Studi di Catanzaro "Magna Græcia"', 'unicz.it', null),
    -- ('unifg', 'Università degli Studi di Foggia', 'unifg.it', null),
    -- ('unimc', 'Università degli Studi di Macerata', 'unimc.it', null),
    -- ('unior', 'Università degli Studi di Napoli "L''Orientale"', 'unior.it', null),
    -- ('uniroma4', 'Università degli Studi di Roma "Foro Italico"', 'uniroma4.it', null),
    -- ('unistrapg', 'Università per Stranieri di Perugia', 'unistrapg.it', null),
    -- ('unistrasi', 'Università per Stranieri di Siena', 'unistrasi.it', null),
    ('luiss', 'Libera Università Internazionale degli Studi Sociali "Guido Carli"', 'luiss.it,luiss.edu', 'IT-62'),
    ('poliba', 'Politecnico di Bari', 'poliba.it', 'IT-75'),
    ('polimi', 'Politecnico di Milano', 'polimi.it', 'IT-25'),
    ('polito', 'Politecnico di Torino', 'polito.it', 'IT-21'),
    ('santanna', 'Scuola superiore di studi universitari e di perfezionamento Sant''Anna', 'santannapisa.it', 'IT-52'),
    ('sns', 'Scuola Normale Superiore', 'sns.it', 'IT-52'),
    ('uniba', 'Università degli Studi di Bari Aldo Moro', 'uniba.it', 'IT-75'),
    ('unibas', 'Università degli Studi della Basilicata', 'unibas.it', 'IT-77'),
    ('unibg', 'Università degli Studi di Bergamo', 'unibg.it', 'IT-25'),
    ('unibo', 'Università degli Studi di Bologna', 'unibo.it', 'IT-45'),
    ('unibs', 'Università degli Studi di Brescia', 'unibs.it', 'IT-25'),
    ('unibz', 'Libera Università di Bolzano', 'unibz.it', null),
    ('unica', 'Università degli Studi di Cagliari', 'unica.it', 'IT-88'),
    ('unical', 'Università degli Studi della Calabria', 'unical.it', 'IT-78'),
    ('unicam', 'Università degli Studi di Camerino', 'unicam.it', 'IT-57'),
    ('unicampania', 'Università degli Studi della Campania "Luigi Vanvitelli"', 'unicampania.it', 'IT-72'),
    ('unicas', 'Università degli Studi di Cassino e del Lazio Meridionale', 'unicas.it', 'IT-62'),
    ('unich', 'Università degli Studi "Gabriele d''Annunzio"', 'unich.it', 'IT-65'),
    ('unict', 'Università degli Studi di Catania', 'unict.it', 'IT-82'),
    ('unife', 'Università degli Studi di Ferrara', 'unife.it', 'IT-45'),
    ('unifi', 'Università degli Studi di Firenze', 'unifi.it', 'IT-52'),
    ('unige', 'Università degli Studi di Genova', 'unige.it', 'IT-42'),
    ('unime', 'Università degli Studi di Messina', 'unime.it', 'IT-82'),
    ('unimi', 'Università degli Studi di Milano', 'unimi.it', 'IT-25'),
    ('unimib', 'Università degli Studi di Milano-Bicocca', 'unimib.it', 'IT-25'),
    ('unimol', 'Università degli Studi del Molise', 'unimol.it', 'IT-67'),
    ('unimore', 'Università degli Studi di Modena e Reggio Emilia', 'unimore.it', 'IT-45'),
    ('unina', 'Università degli Studi di Napoli "Federico II"', 'unina.it', 'IT-72'),
    ('uninsubria', 'Università degli Studi dell''Insubria', 'uninsubria.it', 'IT-25'),
    ('unipa', 'Università degli Studi di Palermo', 'unipa.it', 'IT-82'),
    ('uniparthenope', 'Università degli Studi di Napoli "Parthenope"', 'uniparthenope.it', 'IT-72'),
    ('unipd', 'Università degli Studi di Padova', 'unipd.it', 'IT-34'),
    ('unipg', 'Università degli Studi di Perugia', 'unipg.it', 'IT-55'),
    ('unipi', 'Università degli Studi di Pisa', 'unipi.it', 'IT-52'),
    ('unipr', 'Università degli Studi di Parma', 'unipr.it', 'IT-45'),
    ('unipv', 'Università degli Studi di Pavia', 'unipv.it', 'IT-25'),
    ('unirc', 'Università degli Studi di Reggio Calabria "Mediterranea"', 'unirc.it', 'IT-78'),
    ('uniroma1', 'Università degli Studi di Roma "La Sapienza"', 'uniroma1.it', 'IT-62'),
    ('uniroma2', 'Università degli Studi di Roma Tor Vergata', 'uniroma2.it', 'IT-62'),
    ('uniroma3', 'Università degli Studi Roma Tre', 'uniroma3.it', 'IT-62'),
    ('unisa', 'Università degli Studi di Salerno', 'unisa.it', 'IT-72'),
    ('unisalento', 'Università degli Studi del Salento', 'unisalento.it', 'IT-75'),
    ('unisannio', 'Università degli Studi del Sannio', 'unisannio.it', 'IT-72'),
    ('unisi', 'Università degli Studi di Siena', 'unisi.it', 'IT-52'),
    ('uniss', 'Università degli Studi di Sassari', 'uniss.it', null),
    ('unite', 'Università degli Studi di Teramo', 'unite.it', null),
    ('unitn', 'Università degli Studi di Trento', 'unitn.it', 'IT-32'),
    ('unito', 'Università degli Studi di Torino', 'unito.it', 'IT-21'),
    ('units', 'Università degli Studi di Trieste', 'units.it', null),
    ('unitus', 'Università degli Studi della Tuscia', 'unitus.it', null),
    ('uniud', 'Università degli Studi di Udine', 'uniud.it', 'IT-36'),
    ('uniupo', 'Università degli Studi del Piemonte Orientale "Amedeo Avogadro"', 'uniupo.it', 'IT-21'),
    ('uniurb', 'Università degli Studi di Urbino "Carlo Bo"', 'uniurb.it', null),
    ('univaq', 'Università degli Studi dell''Aquila', 'univaq.it', 'IT-65'),
    ('unive', 'Università Ca'' Foscari di Venezia', 'unive.it', 'IT-34'),
    ('univpm', 'Università Politecnica delle Marche', 'univpm.it', 'IT-57'),
    ('univr', 'Università degli Studi di Verona', 'univr.it', 'IT-34');
