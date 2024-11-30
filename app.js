const { createApp, ref, computed } = Vue;

createApp({
    setup() {
        const searchTerm = ref('');
        const combineSimilarChars = ref(false);
        const posterMode = ref(false);

        const words = ref([
           {
                film: "http://www.wikidata.org/entity/Q14756739",
                filmLabel: "بی‌گناه",
                publicationYear: "1976",
                imdbID: "tt11383472",
                image: "http://commons.wikimedia.org/wiki/Special:FilePath/بی%20گناه.jpg",
                logoCrop: "pct:28.3,84.4,44.4,14.7"
            },
            {
                film: "http://www.wikidata.org/entity/Q5710929",
                filmLabel: "برهنه تا ظهر با سرعت",
                publicationYear: "1976",
                imdbID: "tt0319045",
                image: "http://commons.wikimedia.org/wiki/Special:FilePath/برهنه%20تا%20ظهر%20با%20سرعت.jpg",
                logoCrop: "pct:7,82.1,85.5,7"
            },
            {
                film: "http://www.wikidata.org/entity/Q5867554",
                filmLabel: "شطرنج باد",
                publicationYear: "1976",
                imdbID: "tt0318069",
                image: "http://commons.wikimedia.org/wiki/Special:FilePath/شطرنج%20باد.jpg",
                logoCrop: "pct:10.1,16,39.8,10.1"
            }
        ]);
        
        // تبدیل سال میلادی به شمسی
        const toPersianYear = (gregorianYear) => {
            const gYear = parseInt(gregorianYear, 10);
            if (isNaN(gYear)) return null;
            const shYear = gYear - 621;
            return shYear;
        };

        const getMovieTitleWithYear = (word) => {
            const shamsiYear = toPersianYear(word.publicationYear);
            return shamsiYear ? `${word.filmLabel} (${shamsiYear})` : word.filmLabel;
        };

        const similarCharsMapping = {
            'ط': '[طظ]', 'ظ': '[طظ]', 'ب': '[بپتثن]', 'پ': '[بپتثن]',
            'ت': '[بپتثن]', 'ث': '[بپتثن]', 'ن': '[بپتثن]', 'ج': '[جچحخ]',
            'چ': '[جچحخ]', 'ح': '[جچحخ]', 'خ': '[جچحخ]', 'د': '[دذ]',
            'ذ': '[دذ]', 'ر': '[رزژ]', 'ز': '[رزژ]', 'ژ': '[رزژ]', 'س': '[سش]',
            'ش': '[سش]', 'ص': '[صض]', 'ض': '[صض]', 'ع': '[عغ]',
            'غ': '[عغ]', 'ف': '[فق]', 'ق': '[فق]', 'ک': '[کگ]',
            'گ': '[کگ]'
        };

        const filteredWords = computed(() => {
            if (searchTerm.value.length < 2) return [];
            let modifiedSearchTerm = searchTerm.value;

            if (combineSimilarChars.value) {
                modifiedSearchTerm = modifiedSearchTerm.split('').map(char => similarCharsMapping[char] || char).join('');
            }

            const regex = new RegExp(modifiedSearchTerm, 'i');
            return words.value.filter(word => regex.test(word.filmLabel));
        });

        const getPosterUrl = (filePath, width = 600) => {
            if (!filePath) return 'https://via.placeholder.com/600x900?text=No+Poster';
            const fileName = filePath
                .replace("http://commons.wikimedia.org/wiki/Special:FilePath/", "")
                .replace(/%20/g, '_');
            const md5Hash = md5(fileName);
            const firstChar = md5Hash.charAt(0);
            const firstTwoChars = md5Hash.substring(0, 2);
            return `https://upload.wikimedia.org/wikipedia/commons/thumb/${firstChar}/${firstTwoChars}/${encodeURIComponent(fileName)}/${width}px-${fileName}`;
        };

        const getLogoUrl = (word) => {
            if (!word.image || !word.logoCrop) return 'https://via.placeholder.com/200x300?text=No+Logo';
            const fileName = word.image.split('/').pop();
            return `http://tools.wmflabs.org/zoomviewer/proxy.php?iiif=File:${fileName}/${word.logoCrop}/full/0/default.jpg`;
        };

        const getImageUrl = (word) => {
            return posterMode.value ? getPosterUrl(word.image) : getLogoUrl(word);
        };

        const getImdbLink = (imdbID) => `https://www.imdb.com/title/${imdbID}`;
        const getWikidataLink = (film) => film;

        return { searchTerm, combineSimilarChars, posterMode, filteredWords, getImageUrl, getImdbLink, getWikidataLink, getMovieTitleWithYear };
    }
}).mount('#app');
