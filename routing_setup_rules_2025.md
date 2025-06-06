# Приложение 1 - Правила маршрутизации для клиента
- Подробно о правилах маршрутизации и всех полях можно почитать на [официальном сайте разработчика sing-box](https://sing-box.sagernet.org/configuration/route/rule/).

Правила маршрутизации пишутся в файле формата JSON (JavaScript Object Notation) - это текстовый формат данных, основанный на JavaScript. Как и многие другие текстовые форматы, JSON легко читается людьми. Для описания правил маршрутизации в JSON могут использоваться несколько видов значений:
- **Запись** - это неупорядоченное множество пар **ключ**:**значение**, заключённое в фигурные скобки `«{ }»`. Ключ описывается **строкой**, между ним и значением стоит символ `«:»`. Несколько пар _ключ-значение_ отделяются друг от друга запятыми.
  Например: `"outbound": "proxy"`.
- **Массив** (одномерный) — это упорядоченное множество **значений**. Массив заключается в квадратные скобки `«[ ]»`. Значения разделяются запятыми. Массив может быть пустым, то есть не содержать ни одного значения. Значения в пределах одного массива могут иметь разный тип. 
  Например: `"rules": [ ... ]`.
- Значения могут представлять собой вложенную структуру или содержать массивы.

Общий шаблон записи правил такой:
- Правила записываются в массива `"rules"` через запятую;
- Каждое правило ограничивается фигурными скобками `{ }`;
- Правила применяются сверху внизу по первому совпадению;
- Внутри простые правила для веб-страниц состоят всего из двух полей.
	- Первое - это одно из ключевых слов-шаблонов, задающих логику правила:
		- `"domain"` - правило соответствует, если домен полностью совпадает с шаблоном.
		- `"domain_suffix"` - правило соответствует, если домен запроса соответствует суффиксу. Например: шаблону «[google.com](http://google.com)» соответствует «[www.google.com](http://www.google.com)», «[mail.google.com](http://mail.google.com)» и «[google.com](http://google.com)», но не соответствует «[content-google.com](http://content-google.com)».
		- `"domain_keyword"` - правило соответствует, если домен запроса содержит ключевое слово. Например, шаблону "google" будут соответствовать все сайты из предыдущего примера и даже больше.
		- `"domain_regex"` - позволяет задать [регулярное выражение](https://ru.wikipedia.org/wiki/%D0%A0%D0%B5%D0%B3%D1%83%D0%BB%D1%8F%D1%80%D0%BD%D1%8B%D0%B5_%D0%B2%D1%8B%D1%80%D0%B0%D0%B6%D0%B5%D0%BD%D0%B8%D1%8F) для шаблона домен сайта.
		- `"geosite"` - совпадение по известному списку доменов, например "google" или "yandex".
		- `"geoip"` - совпадение по географическому расположению ip-адреса, например Россия (ru) или Белоруссия (by).
		- `"process_name"` - позволяет указать процессы, для которых будет применяться правило.
	- Вторым ключевым словом каждого правила является указание, что делать, если проверяемый сайт совпал с шаблоном (указание направления трафика (outbound)) : блокировать (block), проксировать (proxy) или пускать напрямую (direct). Например, `"outbound" : "direct"`.
- Правила применяются сверху вниз по первому совпадению. В одном правиле можно указать несколько шаблонов, если для них для всех применяется одно и то же направление трафика.
- При редактировании json файлов можно пользоваться инструментами вроде [_JSON Online Validator_](https://jsonlint.com/) для проверки форматирования.

Общий вид правил:
```JSON
{
    "rules": [
    	{
        	// Ключевые слова правила 1
			// ...
			
			// Направление трафика: direct, block или proxy
			"outbound": "direct"
		},
		{
			// Ключевые слова правила 2
			// "domain": [ "site1.com", "site2.ru" ]
			
			// Направление трафика: direct, block или proxy
			"outbound": "proxy"
		}, 
		{
			//...
		}
	]
}
```

Для записи правил исходящих маршрутов на клиенте можно воспользоваться следующим шаблоном (только в nekoray удаляйте комментарии, он их не поддерживает):
```JSON
{
	// Список правил маршрутизации
	"rules": [
		{
			// Правило 1
		},
		{
			// Правило 2
		},
		{
			// ...
		},
		{
			// Каждое правило может включать в себя следующие поля
			
			// 1. Полное совпадение по доменному имени
			"domain": [
				"google.com"
			],
			
			// 2. Совпадение по окончанию домена
			"domain_suffix": [
				".io", // Сайты, заканчивающиеся на .io
				".live",
				"xn--p1acf", // IP-адреса, содержащие кирилицу и переведённые
				"xn--p1ai",  // в формат латиницы (.рф, .мвд и т.д.)
			],
			
			// 3. Совпадение по ключевому слову в домене
			"domain_keyword": [
				"google" // Любые сайты, в адресе которых есть "google"
			],
			
			// 4. Совпадение по регулярному выражению
			"domain_regex": [
				".*goog.*\.com" // сайты вида *goog*.com
			],
			
			// 5. Совпадение по списку сайтов или доменов из некоторой базы данных
			"geosite": [
				"private", // частные адреса, включая .local
				"youtube" // Домены youtube
			],
			
			// 6. Совпадение по географическому расположению ip-адреса
			"geoip": [
				"private", // Частные ip-адреса
				"ru", // Россия
				"by"  // Белорусия
			],
			
			// Направление трафика: напрямую
			"outbound": "direct"
		},
		{
			// Проксирование трафика от некоторых приложений
			"outbound": "proxy",
			"process_name": [ 
				"Discord.exe", 
				"firefox.exe"
			]
		}
	]
}
```

- Российские ip адреса на кирилице .рф
  Используйте любой онлайновый punicode-конвертер, чтобы преобразовать их в адреса латиницей. Например, "мвд.рф" будет "xn--b1aew.xn--p1ai"
- geoip - это база данных стран и их ip-адресов. Правила ru - russia, by - belarus. Стран su, рф в этой базе не существует. 
- geosite - это база данных сервисов, например steam. Названий ru, su, by, рф в этой базе не существует.

---

# Приложение 2 - Содержимое файла с настройками маршрутов и конфигурации приложения Nekobox для Android
- Создайте файл "nekobox_backup.json".
- Вставьте в него содержимое ниже и импортируйте в приложении.
- В этом файле содержатся: настройки маршрутизации для маршрутизации сайтов РФ напрямую (а не через прокси), исправление косяка с маршрутом "geoip:ru" и включённые настройки VPN/TUN.
- Похоже, nekobox хранит это всё в каком-то зашифрованном виде, ну или у меня что-то криво отображается.
```
{
  "version": 1,
  "rules": [
    "AQAAAAAAAAAKAAAAQgBsAG8AYwBrACAAUQBVAEkAQwAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAMAAAA0ADQAMwAAAAAAAAAAAAAAAwAAAHUAZABwAAAAAAAAAAAAAAAAAAAAAAAAAP7_________AAAAAA",
    "AgAAAAAAAAATAAAAEQQ7BD4EOgQ4BEAEPgQyBDAEQgRMBCAAQAQ1BDoEOwQwBDwEQwQAAAIAAAAAAAAAAQAAABgAAABnAGUAbwBzAGkAdABlADoAYwBhAHQAZQBnAG8AcgB5AC0AYQBkAHMALQBhAGwAbAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA_v________8AAAAA",
    "AwAAAAAAAAAVAAAAEQQ7BD4EOgQ4BEAEPgQyBDAEQgRMBCAAMAQ9BDAEOwQ4BEIEOAQ6BEMEAAADAAAAAAAAAAEAAAA9AAAAZABvAG0AYQBpAG4AOgBhAHAAcABjAGUAbgB0AGUAcgAuAG0AcwAKAGQAbwBtAGEAaQBuADoAZgBpAHIAZQBiAGEAcwBlAC4AaQBvAAoAZABvAG0AYQBpAG4AOgBjAHIAYQBzAGgAbAB5AHQAaQBjAHMALgBjAG8AbQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP7_________AAAAAA",
    "BAAAAAAAAAAZAAAAHwRABDAEMgQ4BDsEPgQgAFAAbABhAHkAIABTAHQAbwByAGUAIAA0BDsETwQgAC1O_VYAAAQAAAAAAAAAAAAAABQAAABkAG8AbQBhAGkAbgA6AGcAbwBvAGcAbABlAGEAcABpAHMALgBjAG4AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    "BQAAAAAAAAAVAAAAHwRABDAEMgQ4BDsEPgQgADQEPgQ8BDUEPQQwBCAANAQ7BE8EIAAtTv1WAAAFAAAAAAAAAAAAAAAKAAAAZwBlAG8AcwBpAHQAZQA6AGMAbgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA__________8AAAAA",
    "BgAAAAAAAAARAAAAHwRABDAEMgQ4BDsEPgQgAEkAUAAgADQEOwRPBCAALU79VgAABgAAAAAAAAAAAAAAAAAAAAAAAAAIAAAAZwBlAG8AaQBwADoAYwBuAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA__________8AAAAA",
    "BwAAAAAAAAAXAAAAHwRABDAEMgQ4BDsEPgQgADQEPgQ8BDUEPQQwBCAANAQ7BE8EIABJAHIAYQBuAAAABwAAAAAAAAAAAAAACgAAAGcAZQBvAHMAaQB0AGUAOgBpAHIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP__________AAAAAA",
    "CAAAAAAAAAATAAAAHwRABDAEMgQ4BDsEPgQgAEkAUAAgADQEOwRPBCAASQByAGEAbgAAAAgAAAAAAAAAAAAAAAAAAAAAAAAACAAAAGcAZQBvAGkAcAA6AGkAcgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP__________AAAAAA",
    "CQAAAAAAAAAZAAAAHwRABDAEMgQ4BDsEPgQgADQEPgQ8BDUEPQQwBCAANAQ7BE8EIABSAHUAcwBzAGkAYQAAAAoAAAAAAAAAAQAAABMAAABnAGUAbwBzAGkAdABlADoAYwBhAHQAZQBnAG8AcgB5AC0AcgB1AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA__________8AAAAA",
    "CgAAAAAAAAAVAAAAHwRABDAEMgQ4BDsEPgQgAEkAUAAgADQEOwRPBCAAUgB1AHMAcwBpAGEAAAALAAAAAAAAAAEAAAAAAAAAAAAAABEAAABnAGUAbwBpAHAAOgByAHUACgBnAGUAbwBpAHAAOgBiAHkAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA__________8AAAAA",
    "DAAAAAAAAAAdAAAAHwRABDAEMgQ4BDsEMAQgAD4EMQRFBD4ENAQwBCAAIARDBEEEQQQ6BDgERQQgAEEEMAQ5BEIEPgQyBAAADAAAAAAAAAABAAAAKwIAAGsAZQB5AHcAbwByAGQAOgB5AGEAbgBkAGUAeAAKAGsAZQB5AHcAbwByAGQAOgB5AGEAcwB0AGEAdABpAGMACgBrAGUAeQB3AG8AcgBkADoAeQBhAGQAaQAuAHMAawAKAGsAZQB5AHcAbwByAGQAOgB4AG4ALQAtADgAMABhAHMAdwBnAAoAawBlAHkAdwBvAHIAZAA6AHgAbgAtAC0AZAAxAGEAYwBwAGoAeAAzAGYALgB4AG4ALQAtAHAAMQBhAGkACgBrAGUAeQB3AG8AcgBkADoAeABuAC0ALQBjADEAYQB2AGcACgBrAGUAeQB3AG8AcgBkADoAeABuAC0ALQA4ADAAYQBzAGUAaABkAGIACgBrAGUAeQB3AG8AcgBkADoAeABuAC0ALQBwADEAYQBjAGYACgBrAGUAeQB3AG8AcgBkADoAeABuAC0ALQBwADEAYQBpAAoAawBlAHkAdwBvAHIAZAA6AGcAbwBvAGcAbABlAC4AYwBvAG0ACgBrAGUAeQB3AG8AcgBkADoAZwBzAHQAYQB0AGkAYwAuAGMAbwBtAAoAawBlAHkAdwBvAHIAZAA6AHkAYQBoAG8AbwAKAGsAZQB5AHcAbwByAGQAOgBiAGkAbgBnAAoAawBlAHkAdwBvAHIAZAA6AHQAaQBuAGUAeQBlAAoAawBlAHkAdwBvAHIAZAA6AGQAdQBjAGsAZAB1AGMAawBnAG8ACgBrAGUAeQB3AG8AcgBkADoAYQBwAHAAbABlAAoAawBlAHkAdwBvAHIAZAA6AHYAawAuAGMAbwBtAAoAawBlAHkAdwBvAHIAZAA6AHUAcwBlAHIAYQBwAGkALgBjAG8AbQAKAGsAZQB5AHcAbwByAGQAOgB2AGsALQBjAGQAbgAuAG0AZQAKAGsAZQB5AHcAbwByAGQAOgBtAHYAawAuAGMAbwBtAAoAawBlAHkAdwBvAHIAZAA6AHYAawAtAGMAZABuAC4AbgBlAHQACgBrAGUAeQB3AG8AcgBkADoAdgBrAC0AcABvAHIAdABhAGwALgBuAGUAdAAKAGsAZQB5AHcAbwByAGQAOgB2AGsALgBjAGMACgBrAGUAeQB3AG8AcgBkADoAaQBjAHEACgBrAGUAeQB3AG8AcgBkADoAbABpAHYAZQBqAG8AdQByAG4AYQBsAAoAawBlAHkAdwBvAHIAZAA6AG0AaQBjAHIAbwBzAG8AZgB0AAoAawBlAHkAdwBvAHIAZAA6AGwAaQB2AGUALgBjAG8AbQAKAGsAZQB5AHcAbwByAGQAOgBsAG8AZwBpAG4ALgBsAGkAdgBlAAoAawBlAHkAdwBvAHIAZAA6AHQAcgBhAGQAaQBuAGcAdgBpAGUAdwBrAGUAeQB3AG8AcgBkAAoAZABvAG0AYQBpAG4AOgAuAHIAdQAKAGQAbwBtAGEAaQBuADoALgBzAHUACgBkAG8AbQBhAGkAbgA6AC4AYgB5AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA__________8AAAAA"
  ],
  "settings": [
    "CQAAAG0AaQB4AGUAZABQAG8AcgB0AAAABQAAAAQAAAAyMDgw",
    "DAAAAHAAbwByAHQATABvAGMAYQBsAEQAbgBzAAAAAAAFAAAABAAAADY0NTA",
    "DQAAAGkAcwBBAHUAdABvAEMAbwBuAG4AZQBjAHQAAAABAAAAAQAAAAAAAAA",
    "CgAAAG4AaQBnAGgAdABUAGgAZQBtAGUAAAAAAAUAAAABAAAAMAAAAA",
    "CwAAAHMAZQByAHYAaQBjAGUATQBvAGQAZQAAAAUAAAADAAAAdnBuAA",
    "EQAAAHQAdQBuAEkAbQBwAGwAZQBtAGUAbgB0AGEAdABpAG8AbgAAAAUAAAABAAAAMgAAAA",
    "AwAAAG0AdAB1AAAABQAAAAQAAAA5MDAw",
    "DQAAAHMAcABlAGUAZABJAG4AdABlAHIAdgBhAGwAAAAFAAAABAAAADEwMDA",
    "GAAAAHAAcgBvAGYAaQBsAGUAVAByAGEAZgBmAGkAYwBTAHQAYQB0AGkAcwB0AGkAYwBzAAAAAAABAAAAAQAAAAEAAAA",
    "FwAAAHMAaABvAHcARwByAG8AdQBwAEkAbgBOAG8AdABpAGYAaQBjAGEAdABpAG8AbgAAAAEAAAABAAAAAAAAAA",
    "EQAAAGEAbAB3AGEAeQBzAFMAaABvAHcAQQBkAGQAcgBlAHMAcwAAAAEAAAABAAAAAAAAAA",
    "DgAAAG0AZQB0AGUAcgBlAGQATgBlAHQAdwBvAHIAawAAAAAAAQAAAAEAAAAAAAAA",
    "DwAAAHMAaABvAHcARABpAHIAZQBjAHQAUwBwAGUAZQBkAAAAAQAAAAEAAAABAAAA",
    "CQAAAGIAeQBwAGEAcwBzAEwAYQBuAAAAAQAAAAEAAAAAAAAA",
    "DwAAAGIAeQBwAGEAcwBzAEwAYQBuAEkAbgBDAG8AcgBlAAAAAQAAAAEAAAAAAAAA",
    "DwAAAHQAcgBhAGYAZgBpAGMAUwBuAGkAZgBmAGkAbgBnAAAABQAAAAEAAAAxAAAA",
    "EgAAAHIAZQBzAG8AbAB2AGUARABlAHMAdABpAG4AYQB0AGkAbwBuAAAAAAABAAAAAQAAAAAAAAA",
    "CAAAAGkAcAB2ADYATQBvAGQAZQAAAAAABQAAAAEAAAAwAAAA",
    "DQAAAHIAdQBsAGUAcwBQAHIAbwB2AGkAZABlAHIAAAAFAAAAAQAAADAAAAA",
    "AwAAAG0AdQB4AAAABgAAAAAAAAA",
    "BwAAAG0AdQB4AFQAeQBwAGUAAAAFAAAAAQAAADAAAAA",
    "DgAAAG0AdQB4AEMAbwBuAGMAdQByAHIAZQBuAGMAeQAAAAAABQAAAAEAAAA4AAAA",
    "EwAAAGcAbABvAGIAYQBsAEEAbABsAG8AdwBJAG4AcwBlAGMAdQByAGUAAAABAAAAAQAAAAAAAAA",
    "CQAAAHIAZQBtAG8AdABlAEQAbgBzAAAABQAAABwAAABodHRwczovL2Rucy5nb29nbGUvZG5zLXF1ZXJ5",
    "GgAAAGQAbwBtAGEAaQBuAF8AcwB0AHIAYQB0AGUAZwB5AF8AZgBvAHIAXwByAGUAbQBvAHQAZQAAAAAABQAAAAQAAABhdXRv",
    "CQAAAGQAaQByAGUAYwB0AEQAbgBzAAAABQAAAB4AAABodHRwczovLzEyMC41My41My41My9kbnMtcXVlcnkAAA",
    "GgAAAGQAbwBtAGEAaQBuAF8AcwB0AHIAYQB0AGUAZwB5AF8AZgBvAHIAXwBkAGkAcgBlAGMAdAAAAAAABQAAAAQAAABhdXRv",
    "GgAAAGQAbwBtAGEAaQBuAF8AcwB0AHIAYQB0AGUAZwB5AF8AZgBvAHIAXwBzAGUAcgB2AGUAcgAAAAAABQAAAAQAAABhdXRv",
    "EAAAAGUAbgBhAGIAbABlAEQAbgBzAFIAbwB1AHQAaQBuAGcAAAAAAAEAAAABAAAAAQAAAA",
    "DQAAAGUAbgBhAGIAbABlAEYAYQBrAGUARABuAHMAAAABAAAAAQAAAAAAAAA",
    "DwAAAGEAcABwAGUAbgBkAEgAdAB0AHAAUAByAG8AeAB5AAAAAQAAAAEAAAAAAAAA",
    "CwAAAGEAbABsAG8AdwBBAGMAYwBlAHMAcwAAAAEAAAABAAAAAAAAAA",
    "EQAAAGMAbwBuAG4AZQBjAHQAaQBvAG4AVABlAHMAdABVAFIATAAAAAUAAAAZAAAAaHR0cDovL2NwLmNsb3VkZmxhcmUuY29tLwAAAA",
    "DwAAAGEAYwBxAHUAaQByAGUAVwBhAGsAZQBMAG8AYwBrAAAAAQAAAAEAAAAAAAAA",
    "DgAAAGUAbgBhAGIAbABlAEMAbABhAHMAaABBAFAASQAAAAAAAQAAAAEAAAAAAAAA",
    "FAAAAHQAYwBwAEsAZQBlAHAAQQBsAGkAdgBlAEkAbgB0AGUAcgB2AGEAbAAAAAAABQAAAAIAAAAxNQAA",
    "DQAAAGEAcABwAFQATABTAFYAZQByAHMAaQBvAG4AAAAFAAAAAwAAADEuMgA",
    "DQAAAHMAaABvAHcAQgBvAHQAdABvAG0AQgBhAHIAAAABAAAAAQAAAAAAAAA",
    "FgAAAGEAbABsAG8AdwBJAG4AcwBlAGMAdQByAGUATwBuAFIAZQBxAHUAZQBzAHQAAAAAAAEAAAABAAAAAAAAAA",
    "CAAAAGwAbwBnAEwAZQB2AGUAbAAAAAAABQAAAAEAAAAyAAAA",
    "CQAAAHAAcgBvAHgAeQBBAHAAcABzAAAAAQAAAAEAAAABAAAA",
    "CgAAAGIAeQBwAGEAcwBzAE0AbwBkAGUAAAAAAAEAAAABAAAAAAAAAA",
    "CgAAAGkAbgBkAGkAdgBpAGQAdQBhAGwAAAAAAAUAAABJAAAAY29tLmRpc2NvcmQKb3JnLm1vemlsbGEuZmlyZWZveApjb20uZ29vZ2xlLmFuZHJvaWQueW91dHViZQphbmRkZWEueW91dHViZQAAAA",
    "CQAAAHAAcgBvAGYAaQBsAGUASQBkAAAABAAAAAgAAAAAAAAAAAAAAQ",
    "DAAAAHAAcgBvAGYAaQBsAGUARwByAG8AdQBwAAAAAAAEAAAACAAAAAAAAAAAAAAB",
    "DgAAAHAAcgBvAGYAaQBsAGUAQwB1AHIAcgBlAG4AdAAAAAAABAAAAAgAAAAAAAAAAAAAAQ"
  ]
}
```

---

# Информация о настройке маршрутизации взята из данного [репозитория](https://github.com/EmptyLibra/Configure-Xray-with-VLESS-Reality-on-VPS-server/tree/master)


