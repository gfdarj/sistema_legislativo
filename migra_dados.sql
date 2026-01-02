---
--- MIGRA OS DADOS DAS EMENTAS E PROJETOS DE LEI
---

delete from www_autor;

insert into www_autor (nome, sexo, ativo)
	select DISTINCT nome, 'M', TRUE
	from autores
;


---
delete from www_proposicao;

insert into www_proposicao (numero, numero_formatado, ementa, data_publicacao, link_proposicao, tipo_id)
	select substr(p.numero, 1, 11), p.numero_formatado, p.ementa, IFNULL(p.data_publicacao, "01/01/2025"), p.link, tp.id
	from projetos_de_lei p 
	inner join www_tipoproposicao tp on p.tipo = tp.sigla
	--where data_publicacao is NULL
;

select * from www_proposicao where tipo_id not in (select distinct sigla from www_tipoproposicao)


---
delete from www_proposicao_autores;

insert into www_proposicao_autores (proposicao_id, autor_id)
	select prop.numero, a.id
	from projetos_de_lei p 
	inner join www_autor a on p.autor = a.nome
	inner join www_proposicao prop on prop.numero = substr(p.numero, 1, 11) 
;


update www_autor set ativo = FALSE;



